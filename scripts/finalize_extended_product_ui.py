#!/usr/bin/env python3
"""Replace the inherited upstream presentation with ClipCascade Extended's product UI."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def remove_between(text: str, start_marker: str, end_marker: str, label: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: start marker missing")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:start] + text[end:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    root = parser.parse_args().destination.resolve()
    path = root / "App.js"
    text = path.read_text(encoding="utf-8")

    text = replace_once(text, "  Linking,\n", "", "remove inherited Linking import")
    text = replace_once(
        text,
        "  StatusBar,\n} from 'react-native';",
        "  StatusBar,\n  PlatformColor,\n} from 'react-native';",
        "PlatformColor import",
    )
    text = replace_once(
        text,
        "import StartForegroundService from './StartForegroundService';",
        """import StartForegroundService from './StartForegroundService';
import ExtendedControlPanel from './ExtendedControlPanel';
import { getExtendedStrings, localizeRuntimeMessage } from './ExtendedI18n';""",
        "Extended UI imports",
    )

    # Remove the earlier partial setup dictionary. The complete dictionary now lives in ExtendedI18n.js.
    setup_start = text.find("const EXTENDED_SETUP_TEXT = (() => {")
    if setup_start >= 0:
        setup_end = text.find("})();", setup_start)
        if setup_end < 0:
            raise RuntimeError("partial setup localization block is unterminated")
        text = text[:setup_start] + text[setup_end + len("})();"):]

    text = replace_once(
        text,
        "// Main App\nexport default function App() {",
        """const EXTENDED_TEXT = getExtendedStrings();

// Main App
export default function App() {""",
        "Extended localization constant",
    )

    for obsolete in (
        "  const [newVersionAvailable, setNewVersionAvailable] = useState([false, '']);\n",
        "  const [donateUrl, setDonateUrl] = useState(null);\n",
        "  const VERSION_URL =\n    'https://raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/version.json';\n",
        "  const GITHUB_URL = 'https://github.com/Sathvik-Rao/ClipCascade';\n",
        "  const RELEASE_URL =\n    'https://github.com/Sathvik-Rao/ClipCascade/releases/latest';\n",
        "  const HELP_URL = `${GITHUB_URL}/blob/main/README.md`;\n",
        "  const METADATA_URL =\n    'https://raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/metadata.json';\n",
    ):
        if obsolete not in text:
            raise RuntimeError(f"inherited UI marker missing: {obsolete!r}")
        text = text.replace(obsolete, "", 1)

    update_start = "        // check for new version\n"
    outer_catch = "      } catch (e) {\n        setInItError([true, e.message]);"
    text = remove_between(text, update_start, outer_catch, "remove upstream update/funding fetches")

    view_start = text.find("  // view\n")
    styles_start = text.find("// view styles", view_start)
    if view_start < 0 or styles_start < 0:
        raise RuntimeError("App view/style markers missing")

    new_view = r'''  const checkboxRow = (label, key) => (
    <View style={styles.checkboxRow}>
      <Text style={styles.label}>{label}</Text>
      <CheckBox
        value={data[key] === 'true'}
        tintColors={{ true: '#2e7d32', false: '#80868b' }}
        onValueChange={newValue => handleInputChange(key, String(newValue))}
      />
    </View>
  );

  const fieldRow = (label, key, options = {}) => (
    <View style={styles.fieldBlock}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={key === 'password' ? password : data[key]}
        onChangeText={value => {
          if (key === 'password') {
            setPassword(value);
          } else {
            handleInputChange(key, options.trim ? value.trim() : value);
          }
        }}
        secureTextEntry={key === 'password'}
        autoCapitalize="none"
        keyboardType={options.numeric ? 'numeric' : 'default'}
        placeholderTextColor={PlatformColor('?android:attr/textColorHint')}
      />
    </View>
  );

  if (initError[0]) {
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.centered}>
          <Text style={styles.appTitle}>{APP_NAME}</Text>
          <Text style={styles.subtitle}>{EXTENDED_TEXT.appSubtitle}</Text>
          <Text selectable style={styles.errorText}>
            {EXTENDED_TEXT.initError}: {String(initError[1])}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar
        backgroundColor={PlatformColor('?android:attr/colorBackground')}
        barStyle="default"
      />
      {enableLoadingPage && (
        <View style={styles.centered}>
          <Text style={styles.appTitle}>{APP_NAME}</Text>
          <Text style={styles.subtitle}>{EXTENDED_TEXT.appSubtitle}</Text>
          <ActivityIndicator size="large" />
          <Text style={styles.statusText}>
            {localizeRuntimeMessage(loadingPageMessage, EXTENDED_TEXT)}
          </Text>
        </View>
      )}

      {enableLoginPage && (
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.appTitle}>{APP_NAME}</Text>
          <Text style={styles.subtitle}>{EXTENDED_TEXT.appSubtitle}</Text>
          {fieldRow(EXTENDED_TEXT.username, 'username')}
          {fieldRow(EXTENDED_TEXT.password, 'password')}
          {fieldRow(EXTENDED_TEXT.serverUrl, 'server_url', { trim: true })}
          {checkboxRow(EXTENDED_TEXT.encryption, 'cipher_enabled')}

          {loginStatusMessage !== '' && (
            <Text selectable style={styles.statusText}>
              {localizeRuntimeMessage(loginStatusMessage, EXTENDED_TEXT)}
            </Text>
          )}

          <TouchableOpacity style={styles.primaryButton} onPress={() => handleLogin(null, null)}>
            <Text style={styles.buttonText}>{EXTENDED_TEXT.login}</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setShowExtraConfig(!showExtraConfig)}>
            <Text style={styles.linkText}>
              {showExtraConfig ? EXTENDED_TEXT.hideExtra : EXTENDED_TEXT.showExtra}
            </Text>
          </TouchableOpacity>

          {showExtraConfig && (
            <View style={styles.card}>
              {fieldRow(EXTENDED_TEXT.hashRounds, 'hash_rounds', { numeric: true, trim: true })}
              {fieldRow(EXTENDED_TEXT.salt, 'salt')}
              {checkboxRow(EXTENDED_TEXT.savePassword, 'save_password')}
              {fieldRow(EXTENDED_TEXT.maxClipboard, 'max_clipboard_size_local_limit_bytes', {
                numeric: true,
                trim: true,
              })}
              {checkboxRow(EXTENDED_TEXT.relaunchOnBoot, 'relaunch_on_boot')}
              {checkboxRow(
                EXTENDED_TEXT.statusNotification,
                'enable_websocket_status_notification',
              )}
              {checkboxRow(EXTENDED_TEXT.periodicChecks, 'enable_periodic_checks')}
              {checkboxRow(EXTENDED_TEXT.imageSharing, 'enable_image_sharing')}
              {checkboxRow(EXTENDED_TEXT.fileSharing, 'enable_file_sharing')}
            </View>
          )}
        </ScrollView>
      )}

      {enableWSPage && (
        <ScrollView contentContainerStyle={styles.container}>
          <Text style={styles.appTitle}>{APP_NAME}</Text>
          <Text style={styles.subtitle}>{EXTENDED_TEXT.appSubtitle}</Text>

          <TouchableOpacity
            style={wsIsRunning === 'true' ? styles.stopButton : styles.primaryButton}
            onPress={foregroundService}
          >
            <Text style={styles.buttonText}>
              {wsIsRunning === 'true' ? EXTENDED_TEXT.stop : EXTENDED_TEXT.start}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.dangerButton} onPress={logout}>
            <Text style={styles.buttonText}>{EXTENDED_TEXT.logout}</Text>
          </TouchableOpacity>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>{EXTENDED_TEXT.connectionStatus}</Text>
            <Text selectable style={styles.statusText}>
              {localizeRuntimeMessage(wsPageMessage, EXTENDED_TEXT)}
            </Text>
            {wsPageP2PMessage !== '' && (
              <>
                <Text style={styles.cardTitle}>{EXTENDED_TEXT.p2pStatus}</Text>
                <Text selectable style={styles.statusText}>
                  {localizeRuntimeMessage(wsPageP2PMessage, EXTENDED_TEXT)}
                </Text>
              </>
            )}
          </View>

          {enableFilesDownloadButton && (
            <TouchableOpacity style={styles.primaryButton} onPress={downloadFiles}>
              <Text style={styles.buttonText}>{EXTENDED_TEXT.downloadFiles}</Text>
            </TouchableOpacity>
          )}

          <ExtendedControlPanel
            NativeBridgeModule={NativeBridgeModule}
            notifee={notifee}
          />
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

'''

    new_styles = r'''// view styles
const styles = StyleSheet.create({
  screen: {
    flex: 1,
    paddingTop: StatusBar.currentHeight,
    backgroundColor: PlatformColor('?android:attr/colorBackground'),
  },
  container: {
    padding: 18,
    paddingBottom: 48,
    backgroundColor: PlatformColor('?android:attr/colorBackground'),
  },
  centered: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: PlatformColor('?android:attr/colorBackground'),
  },
  appTitle: {
    color: PlatformColor('?android:attr/textColorPrimary'),
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    color: PlatformColor('?android:attr/textColorSecondary'),
    fontSize: 14,
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 20,
  },
  fieldBlock: { marginBottom: 12 },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  label: {
    flex: 1,
    color: PlatformColor('?android:attr/textColorPrimary'),
    fontSize: 15,
    lineHeight: 21,
    marginBottom: 5,
  },
  input: {
    color: PlatformColor('?android:attr/textColorPrimary'),
    backgroundColor: PlatformColor('?android:attr/editTextBackground'),
    borderWidth: 1,
    borderColor: PlatformColor('?android:attr/listDivider'),
    paddingHorizontal: 10,
    paddingVertical: 9,
    borderRadius: 8,
  },
  card: {
    marginTop: 12,
    padding: 14,
    borderRadius: 12,
    backgroundColor: PlatformColor('?android:attr/colorBackgroundFloating'),
    borderWidth: 1,
    borderColor: PlatformColor('?android:attr/listDivider'),
  },
  cardTitle: {
    color: PlatformColor('?android:attr/textColorPrimary'),
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
  },
  statusText: {
    color: PlatformColor('?android:attr/textColorPrimary'),
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'left',
    marginVertical: 8,
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: '#2457a6',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: 6,
  },
  stopButton: {
    backgroundColor: '#8c2330',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: 6,
  },
  dangerButton: {
    backgroundColor: '#6f1d28',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: 6,
  },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: '600' },
  linkText: {
    color: PlatformColor('?android:attr/textColorLink'),
    textDecorationLine: 'underline',
    textAlign: 'center',
    marginVertical: 12,
    fontSize: 16,
  },
});
'''

    text = text[:view_start] + new_view + new_styles
    for forbidden in (
        "New version available!",
        "GITHUB",
        "DONATE",
        "HOMEPAGE",
        "Automatic Clipboard Monitoring Setup",
        "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/version.json",
        "raw.githubusercontent.com/Sathvik-Rao/ClipCascade/main/metadata.json",
        "adb -d shell am force-stop",
        "EXTENDED_SETUP_TEXT",
    ):
        if forbidden in text:
            raise RuntimeError(f"inherited UI residue remained: {forbidden}")

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
