# Wenxing / CBP braille display driver for NVDA.

from ctypes import (
	POINTER,
	Structure,
	WinDLL,
	addressof,
	byref,
	c_ubyte,
	c_uint,
	c_ulong,
	c_long,
	c_void_p,
	create_string_buffer,
	sizeof,
	wstring_at,
)
from ctypes import wintypes
import threading
import time

import braille
import inputCore
from logHandler import log


DEVICE_INTERFACE_GUID = "{58D07210-27C1-11DD-BD0B-0800200C9A66}"
USB_ID = "VID_04D8&PID_0053"
CELL_COUNT = 40
PACKET_SIZE = 64
OUT_PIPE = 0x01
IN_PIPE = 0x81
IDLE_KEY = 255
POLL_INTERVAL = 0.05

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
FILE_FLAG_OVERLAPPED = 0x40000000
INVALID_HANDLE_VALUE = c_void_p(-1).value

DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
ERROR_NO_MORE_ITEMS = 259


kernel32 = WinDLL("kernel32", use_last_error=True)
setupapi = WinDLL("setupapi", use_last_error=True)
winusb = WinDLL("winusb", use_last_error=True)


class GUID(Structure):
	_fields_ = (
		("Data1", c_ulong),
		("Data2", wintypes.WORD),
		("Data3", wintypes.WORD),
		("Data4", c_ubyte * 8),
	)


class SP_DEVICE_INTERFACE_DATA(Structure):
	_fields_ = (
		("cbSize", c_ulong),
		("InterfaceClassGuid", GUID),
		("Flags", c_ulong),
		("Reserved", c_void_p),
	)


ole32 = WinDLL("ole32", use_last_error=True)
ole32.CLSIDFromString.argtypes = (wintypes.LPCOLESTR, POINTER(GUID))
ole32.CLSIDFromString.restype = c_long

setupapi.SetupDiGetClassDevsW.argtypes = (POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, c_ulong)
setupapi.SetupDiGetClassDevsW.restype = c_void_p
setupapi.SetupDiEnumDeviceInterfaces.argtypes = (
	c_void_p,
	c_void_p,
	POINTER(GUID),
	c_uint,
	POINTER(SP_DEVICE_INTERFACE_DATA),
)
setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = (
	c_void_p,
	POINTER(SP_DEVICE_INTERFACE_DATA),
	c_void_p,
	c_uint,
	POINTER(c_uint),
	c_void_p,
)
setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
setupapi.SetupDiDestroyDeviceInfoList.argtypes = (c_void_p,)
setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

kernel32.CreateFileW.argtypes = (
	wintypes.LPCWSTR,
	c_uint,
	c_uint,
	c_void_p,
	c_uint,
	c_uint,
	c_void_p,
)
kernel32.CreateFileW.restype = c_void_p
kernel32.CloseHandle.argtypes = (c_void_p,)
kernel32.CloseHandle.restype = wintypes.BOOL

winusb.WinUsb_Initialize.argtypes = (c_void_p, POINTER(c_void_p))
winusb.WinUsb_Initialize.restype = wintypes.BOOL
winusb.WinUsb_Free.argtypes = (c_void_p,)
winusb.WinUsb_Free.restype = wintypes.BOOL
winusb.WinUsb_WritePipe.argtypes = (c_void_p, c_ubyte, c_void_p, c_uint, POINTER(c_uint), c_void_p)
winusb.WinUsb_WritePipe.restype = wintypes.BOOL
winusb.WinUsb_ReadPipe.argtypes = (c_void_p, c_ubyte, c_void_p, c_uint, POINTER(c_uint), c_void_p)
winusb.WinUsb_ReadPipe.restype = wintypes.BOOL


def _winErr():
	return "Win32={}".format(kernel32.GetLastError())


def _guidFromString(value):
	guid = GUID()
	if ole32.CLSIDFromString(value, byref(guid)) < 0:
		raise RuntimeError("Invalid GUID {}".format(value))
	return guid


def _isInvalidHandle(handle):
	return not handle or handle == INVALID_HANDLE_VALUE


def _findDevicePath():
	"""Find the WinUSB device path exposed by the Wenxing driver INF."""
	guid = _guidFromString(DEVICE_INTERFACE_GUID)
	infoSet = setupapi.SetupDiGetClassDevsW(byref(guid), None, None, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
	if _isInvalidHandle(infoSet):
		raise RuntimeError("SetupDiGetClassDevsW failed: {}".format(_winErr()))
	try:
		index = 0
		while True:
			interfaceData = SP_DEVICE_INTERFACE_DATA()
			interfaceData.cbSize = sizeof(SP_DEVICE_INTERFACE_DATA)
			if not setupapi.SetupDiEnumDeviceInterfaces(infoSet, None, byref(guid), index, byref(interfaceData)):
				err = kernel32.GetLastError()
				if err == ERROR_NO_MORE_ITEMS:
					return None
				log.debugWarning("SetupDiEnumDeviceInterfaces failed: Win32={}".format(err))
				index += 1
				continue
			required = c_uint(0)
			setupapi.SetupDiGetDeviceInterfaceDetailW(infoSet, byref(interfaceData), None, 0, byref(required), None)
			if not required.value:
				index += 1
				continue
			buf = create_string_buffer(required.value)
			# SP_DEVICE_INTERFACE_DETAIL_DATA_W.cbSize: 6 on 32-bit, 8 on 64-bit.
			cbSize = 8 if sizeof(c_void_p) == 8 else 6
			c_uint.from_buffer(buf).value = cbSize
			if setupapi.SetupDiGetDeviceInterfaceDetailW(
				infoSet,
				byref(interfaceData),
				buf,
				required,
				byref(required),
				None,
			):
				return wstring_at(c_void_p(addressof(buf) + 4))
			log.debugWarning("SetupDiGetDeviceInterfaceDetailW failed: {}".format(_winErr()))
			index += 1
	finally:
		setupapi.SetupDiDestroyDeviceInfoList(infoSet)


class _WinUsbDevice:
	"""Small WinUSB wrapper for the Wenxing display protocol."""

	def __init__(self):
		self._deviceHandle = None
		self._usbHandle = c_void_p()
		path = _findDevicePath()
		if not path:
			raise RuntimeError("Wenxing display not found")
		handle = kernel32.CreateFileW(
			path,
			GENERIC_READ | GENERIC_WRITE,
			FILE_SHARE_READ | FILE_SHARE_WRITE,
			None,
			OPEN_EXISTING,
			FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED,
			None,
		)
		if _isInvalidHandle(handle):
			raise RuntimeError("CreateFileW failed for {}: {}".format(path, _winErr()))
		self._deviceHandle = handle
		if not winusb.WinUsb_Initialize(handle, byref(self._usbHandle)):
			self.close()
			raise RuntimeError("WinUsb_Initialize failed: {}".format(_winErr()))
		log.info("Opened Wenxing display: {}".format(path))

	def close(self):
		if self._usbHandle:
			try:
				winusb.WinUsb_Free(self._usbHandle)
			except Exception:
				log.debugWarning("WinUsb_Free failed", exc_info=True)
			self._usbHandle = c_void_p()
		if self._deviceHandle and not _isInvalidHandle(self._deviceHandle):
			try:
				kernel32.CloseHandle(self._deviceHandle)
			except Exception:
				log.debugWarning("CloseHandle failed", exc_info=True)
			self._deviceHandle = None

	def writePipe(self, pipe, data):
		buf = (c_ubyte * len(data)).from_buffer_copy(data)
		transferred = c_uint(0)
		if not winusb.WinUsb_WritePipe(self._usbHandle, pipe, buf, len(data), byref(transferred), None):
			raise RuntimeError("WinUsb_WritePipe failed: {}".format(_winErr()))
		if transferred.value != len(data):
			raise RuntimeError("Short WinUSB write: {} of {}".format(transferred.value, len(data)))

	def readPipe(self, pipe, size):
		buf = (c_ubyte * size)()
		transferred = c_uint(0)
		if not winusb.WinUsb_ReadPipe(self._usbHandle, pipe, buf, size, byref(transferred), None):
			raise RuntimeError("WinUsb_ReadPipe failed: {}".format(_winErr()))
		return bytes(bytearray(buf)[: transferred.value])

	def display(self, cells):
		# Display packet: 0x80 followed by up to 40 braille cells, padded to 64 bytes.
		packet = bytearray(PACKET_SIZE)
		packet[0] = 0x80
		for index, cell in enumerate(cells[:CELL_COUNT]):
			packet[index + 1] = cell & 0xFF
		self.writePipe(OUT_PIPE, bytes(packet))

	def getKey(self):
		# Key query: write 0x81, read a 64-byte response whose second byte is the key code.
		self.writePipe(OUT_PIPE, b"\x81")
		response = self.readPipe(IN_PIPE, PACKET_SIZE)
		if len(response) < 2 or response[0] != 0x81:
			raise RuntimeError("Invalid key response: {!r}".format(response[:4]))
		return response[1]


class BrailleDisplayDriver(braille.BrailleDisplayDriver):
	name = "wenxing"
	description = _("Wenxing / CBP Braille Display")
	isThreadSafe = True
	supportsAutomaticDetection = False

	@classmethod
	def check(cls):
		return _findDevicePath() is not None

	def __init__(self, port="auto"):
		super(BrailleDisplayDriver, self).__init__()
		self.numCells = CELL_COUNT
		self._lock = threading.RLock()
		self._dev = _WinUsbDevice()
		self._lastKey = IDLE_KEY
		self._stopEvent = threading.Event()
		self._keyThread = threading.Thread(target=self._keyLoop, name="WenxingBrailleKeyPoll")
		self._keyThread.daemon = True
		self._keyThread.start()

	def terminate(self):
		try:
			self._stopEvent.set()
			try:
				self._keyThread.join(0.5)
			except Exception:
				pass
		finally:
			try:
				with self._lock:
					self._dev.close()
			finally:
				super(BrailleDisplayDriver, self).terminate()

	def display(self, cells):
		try:
			with self._lock:
				self._dev.display(cells)
		except Exception:
			log.debugWarning("Wenxing display write failed", exc_info=True)

	def _keyLoop(self):
		# Polling is serialized with display writes because WinUSB access is not guaranteed
		# to be safe across simultaneous reads and writes on this device.
		while not self._stopEvent.is_set():
			try:
				with self._lock:
					key = self._dev.getKey()
				if key == IDLE_KEY:
					self._lastKey = IDLE_KEY
				elif key and key != self._lastKey:
					self._lastKey = key
					try:
						inputCore.manager.executeGesture(InputGesture(key))
					except inputCore.NoInputGestureAction:
						pass
			except Exception:
				log.debugWarning("Wenxing key poll failed", exc_info=True)
				time.sleep(0.5)
			self._stopEvent.wait(POLL_INTERVAL)

	gestureMap = inputCore.GlobalGestureMap(
		{
			"globalCommands.GlobalCommands": {
				"braille_routeTo": ("br(wenxing):routing",),
				"braille_previousLine": ("br(wenxing):leftOuter",),
				"braille_scrollBack": ("br(wenxing):leftMiddle",),
				"review_top": ("br(wenxing):leftInner",),
				"braille_nextLine": ("br(wenxing):rightOuter",),
				"braille_scrollForward": ("br(wenxing):rightMiddle",),
				"review_bottom": ("br(wenxing):rightInner",),
			},
		},
	)


class InputGesture(braille.BrailleDisplayGesture):
	source = BrailleDisplayDriver.name

	def __init__(self, key):
		super(InputGesture, self).__init__()
		if 1 <= key <= CELL_COUNT:
			self.id = "routing"
			self.routingIndex = key - 1
		else:
			self.id = {
				41: "leftOuter",
				42: "leftMiddle",
				43: "leftInner",
				44: "rightOuter",
				45: "rightMiddle",
				46: "rightInner",
			}.get(key, "unknown{}".format(key))
