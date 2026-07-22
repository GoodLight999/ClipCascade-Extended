/* eslint-env jest */

jest.mock('@notifee/react-native', () => ({
  __esModule: true,
  default: {
    cancelAllNotifications: jest.fn(async () => undefined),
    cancelNotification: jest.fn(async () => undefined),
    createChannel: jest.fn(async config => config.id),
    displayNotification: jest.fn(async () => undefined),
    openBatteryOptimizationSettings: jest.fn(async () => undefined),
    openPowerManagerSettings: jest.fn(async () => undefined),
    registerForegroundService: jest.fn(),
    stopForegroundService: jest.fn(async () => undefined),
  },
  AndroidImportance: {
    LOW: 2,
    DEFAULT: 3,
    HIGH: 4,
  },
}));

jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock('@react-native-community/checkbox', () => 'CheckBox');

jest.mock('@react-native-documents/picker', () => ({
  pickDirectory: jest.fn(async () => null),
  isCancel: jest.fn(() => false),
}));

jest.mock('@react-native-module/pbkdf2', () => ({
  pbkdf2: jest.fn((password, salt, rounds, length, digest, callback) => {
    callback(null, Buffer.alloc(length));
  }),
}));

jest.mock('@react-native-clipboard/clipboard', () => ({
  __esModule: true,
  default: {
    setString: jest.fn(),
    getString: jest.fn(async () => ''),
  },
}));

jest.mock('react-native-aes-gcm-crypto', () => ({
  __esModule: true,
  default: {
    encrypt: jest.fn(async () => ({iv: '', content: '', tag: ''})),
    decrypt: jest.fn(async () => ''),
  },
}));

jest.mock('react-native-webrtc', () => {
  class MockDataChannel {
    readyState = 'closed';
    send = jest.fn();
    close = jest.fn();
  }

  class MockPeerConnection {
    createDataChannel = jest.fn(() => new MockDataChannel());
    createOffer = jest.fn(async () => ({}));
    createAnswer = jest.fn(async () => ({}));
    setLocalDescription = jest.fn(async () => undefined);
    setRemoteDescription = jest.fn(async () => undefined);
    addIceCandidate = jest.fn(async () => undefined);
    close = jest.fn();
  }

  return {
    RTCPeerConnection: MockPeerConnection,
    RTCIceCandidate: class {},
    RTCSessionDescription: class {},
  };
});

const {NativeModules, PermissionsAndroid} = require('react-native');

NativeModules.NativeBridgeModule = {
  clearCookies: jest.fn(async () => undefined),
  clearImageCache: jest.fn(async () => undefined),
  getFlagsSync: jest.fn(() =>
    JSON.stringify({
      wsIsRunning: 'false',
      wsStatusMessage: '',
      server_mode: 'P2S',
      p2pStatusMessage: '',
      filesAvailableToDownload: 'false',
    }),
  ),
  getReliabilityStatus: jest.fn(async () =>
    JSON.stringify({
      packageName: 'com.clipcascade.extended',
      notificationAccess: false,
      readLogs: false,
      overlay: false,
      serviceRequested: false,
      connectionStatus: '',
      pendingEvents: 0,
    }),
  ),
  openNotificationListenerSettings: jest.fn(async () => true),
};

NativeModules.ClipboardListener = {
  addListener: jest.fn(),
  removeListeners: jest.fn(),
  startListening: jest.fn(),
  stopListening: jest.fn(),
};

jest.spyOn(PermissionsAndroid, 'request').mockResolvedValue('granted');

global.fetch = jest.fn(async () => ({
  ok: false,
  status: 503,
  text: async () => '',
  json: async () => ({}),
  headers: {
    get: jest.fn(() => null),
  },
}));
