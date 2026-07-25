# ClipCascade Extended — 正本引継ぎ

Last updated: **2026-07-25 JST**

新しいスレッドでは、次の一文だけで本書とリポジトリを正本として再開する。

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

## 1. Authority / active work

- Repository: `GoodLight999/ClipCascade-Extended`
- Active branch: `stability-mobile-otp`
- Draft PR: `#2`
- Package: `com.clipcascade.extended`
- Current version line: `3.2.0-extended.5` / versionCode `320005`
- Fixed signer certificate SHA-256: `2536d65c0e977341d767fd045b3c3f9c40b57bf4bc51959a98232e9f20030bbd`
- Protocol/server authority: `Sathvik-Rao/ClipCascade`
- Android behavior reference: `wuxinkami/ClipCascade_go_fork`
- Shizuku API: `RikkaApps/Shizuku-API`
- Guided Shizuku distribution: `thedjchi/Shizuku`

過去の破綻した派生物、archive、trash、別リポジトリを資料として復活させない。一次資料は本リポジトリ、上記本家、Go版参考実装だけとする。

## 2. Non-negotiable requirements

1. Androidの汎用クリップボード同期を、前景・背景・画面OFF・再接続・プロセス死亡・再起動を含めて安定稼働させる。
2. 通常経路はADB不要。Accessibilityの明示的コピー信号と短時間の透明ActivityでAndroidのクリップボード制限を正規に満たす。
3. Shizukuは一回だけの権限設定補助。READ_LOGSとoverlayが保持された後、通常ランタイムはShizuku Binderへ依存しない。
4. PC ADBは次善策。表示するのは必要な2コマンドだけで、選択・全文コピー可能にする。
5. テキストコピー、Android共有テキスト、画像クリップボード、画像共有、単一／複数ファイル共有を送信対象にする。
6. 本家サーバー、本家デスクトップ、P2S/STOMP、P2P/WebRTC、暗号化、受信画像／ファイルとの互換性を維持する。
7. UI全体を日本語・英語・簡体字中国語へ統一する。追加部分だけ別言語にしない。
8. ダークモードでも診断・本文・入力・ダイアログを明瞭に読める配色にする。
9. 本家由来の更新告知、更新確認通信、外部リンク群、寄付、旧ADB説明を生成物へ残さない。
10. 固定署名・単調増加versionCodeで上書き更新を維持する。
11. OTP/SMS/emailの自動抽出は、汎用クリップボードの実機受入完了まで実装対象外とする。
12. 表示値の羅列ではなく実経路を検査する全自動デバッグを搭載する。
13. 挙動・証拠・受入状態が変わるたびに本書と `WORKLOG.md` を更新する。

## 3. Source architecture

本プロジェクトは、固定した本家モバイルソースをCIで取得し、Extendedのoverlayと決定的finalizerを適用して生成する。

- Pin: `UPSTREAM.lock`
- Entry point: `scripts/materialize_upstream.sh`
- Overlay source: `overlay/`
- Static architecture guards: `scripts/validate_*.py`
- Android CI: `.github/workflows/android-ci.yml`

### Cleanliness rule

- 最終設計を一度生成して後段で打ち消す補正工程を作らない。
- finalizerは一つの責務だけを持ち、最終コードを直接生成する。
- 同一パスを複数工程で往復編集するときは統合を優先する。
- 文字列検索だけでなく、純粋関数・Android unit test・Jest・エミュレータ実経路で証明する。
- 生成物が通るだけでなく、生成工程自体が読み解けることを品質条件とする。

現在、P2P互換性とExtended UIについて、後段で打ち消していた補正工程を廃止し、それぞれ一つの最終生成工程へ統合済み。

## 4. Android clipboard acquisition

### Primary path

1. `ClipCascadeAccessibilityService` がコピー操作を示すAccessibilityイベントを分類する。
2. `ClipboardCaptureCoordinator` が重複要求を直列化する。
3. `ClipboardFloatingActivity` を透明・短時間・フォーカス可能なActivityとして表示する。
4. Androidが前景アクセスとして許可した期間にクリップボードを読む。
5. 最初の空読取／拒否は短い間隔で一回再試行する。
6. JS listenerが未準備なら `PendingReactEventStore` へ永続化し、準備後に順序を保ってdrainする。
7. Foreground Serviceが失われていれば、明示的コピーで表示されたActivityからHeadless JS復旧を試みる。

### Fallback path

- READ_LOGSが付与されている場合だけログ信号を補助利用する。
- READ_LOGSは必須条件ではない。
- Shizuku／ADB設定後も通常コピー経路はShizukuへ依存しない。

## 5. Shizuku setup contract

UI側は `ShizukuSetupPolicy.js` で次の状態を明確に分離する。

- `already-configured`: READ_LOGSとoverlayが保持済み。Shizuku停止中でも成功扱い。
- `not-installed`: インストール／入手導線を表示。
- `not-running`: サービス起動ガイドを表示。
- `permission-required`: Binderは生きているがExtended未認可。
- `ready-to-apply`: 認可済みで一回設定を実行可能。

ネイティブ側はSticky Binder受信、Binder死亡、bounded wait、UserService世代管理、コマンド終了値、Android側の実権限を検証する。設定完了後にUserServiceを削除する。

PC ADB fallbackは次の2コマンドだけを表示する。

```text
adb shell pm grant com.clipcascade.extended android.permission.READ_LOGS
adb shell appops set com.clipcascade.extended android:system_alert_window allow
```

## 6. Android Share and images/files

- `ACTION_SEND`, `ACTION_SEND_MULTIPLE`, `ACTION_PROCESS_TEXT` を処理する。
- テキストは `CharSequence` として受け、`text/plain` に限定しない。
- 画像／ファイルのContent URIは権限が有効な間に `cache/shared_outbound` へ退避する。
- 退避後はExtended FileProvider URIを送信キューへ渡す。
- 複数ファイル、容量上限、期限清掃、部分失敗清掃、短時間重複抑止を実装する。
- 未対応共有はpending状態を解除し、誤自動起動を残さない。
- logcatへ共有内容そのものを出さず、event種別・件数・保留件数だけを証跡化する。

## 7. Transport reliability

### Durable outbound queue

- server mode・URL・usernameでscopeする。
- offline／process deathを越えて保持する。
- 失敗回数・backoff・drop理由を診断へ残す。
- 新規イベントと既存queue headの順序を逆転させない。

### P2S

- 本家 `/clipsocket`、`/app/cliptext`、`/user/queue/cliptext` と互換。
- `metadata.extendedDeliveryId` の自己echoまでqueue headを解放しない。
- timeout、late ACK、再試行を処理する。
- 受信復号失敗を分類し、同一事故の画面表示を30秒単位で一件へ集約する。
- 発生回数・時刻・詳細を診断へ保存し、正常受信で即時リセットする。

### P2P

- 本家のOFFER／ANSWERへ任意compatibility metadataを追加するだけで、未知メッセージ種別を追加しない。
- クリップボードDataChannelへ独自control frameを送信しない。
- 暗号モード不一致やAEAD復号失敗はPeer単位で隔離する。
- 互換Peerとの通信を継続し、隔離Peerを送信・再接続対象から除外する。
- 互換性情報にパスワード由来fingerprintを含めない。
- fragmentの順序、重複、競合、TTL、容量、backpressureを検証する。

## 8. Foreground Service reliability

- Foreground handlerとネットワーク実体を一つに限定する。
- 二重ランタイム要求はleaseで抑止し、instance IDと抑止時刻を保存する。
- 5秒heartbeatを保存し、同期要求中に15秒以上古ければ自動診断FAIL。
- poll loop、timer、WebRTC callback、signaling reconnectの例外を監督する。
- 停止待ちはbounded timeoutとし、永久待ちを禁止する。
- loop終了時はlistener、timer、connection、foreground notification、runtime leaseを必ず解放する。
- 画面外から禁止されるForeground Service開始を無理に行わず、次の明示的コピーで可視Activityから復旧する。

## 9. Product UI / localization

- Extended専用のログイン、詳細設定、同期、端末設定、診断UIを生成する。
- 本家更新確認通信と外部リンク群は生成時に除去し、validatorでも禁止する。
- 日本語・英語・簡体字中国語は同一キー集合を持つ。
- ログイン、接続、P2P、通知、ダウンロード、診断、Shizuku、失敗表示までローカライズする。
- 例外コード・プロトコル値・生JSONは診断性のため機械可読のまま保持する。
- 診断カードはOEMテーマ属性に依存せず、明暗双方でコントラスト比7以上をJestで検証する。
- ADBと診断ダイアログは選択可能で、全文コピーを一タップで行える。

## 10. One-tap automatic debugging

「全自動デバッグ」は次を能動的に検査・採取し、PASS／要確認／FAILへ分類する。

- ネイティブ→Reactイベント実配送と2秒timeout。
- JS listener readinessとpending native events。
- Accessibility有効状態、最後の信号、取得コーディネーター。
- 前景クリップボード実読取、payload有無、MIME、URI件数。
- durable outbound queueの件数・状態・失敗。
- Android Shareのpending／staging／cache件数・容量。
- Foreground Service heartbeat、instance、重複抑止、detached callback error、復旧状態。
- P2P候補／互換／非互換数、signaling／peer setup／peer operationの最終エラー。
- P2S受信事故code・回数・時刻・詳細。
- Shizuku Binder／認可／READ_LOGS／overlay。
- package、version、SDK、manufacturer、model。

レポートは全文コピー可能だが、password、hashed password、username、server URL、WebSocket URL、saltを含めない。

## 11. Automated verification

CIは次を実行する。

1. 固定upstreamの取得とoverlay生成。
2. canonical-source／architecture／forbidden-residue validators。
3. JavaScript lintとJest。
4. Android lint、Kotlin unit tests、assembleRelease。
5. package、version、署名、DEX marker、禁止文字列、SHA-256検証。
6. API 35 / API 36 emulator smoke。

エミュレータsmokeは次を実行する。

- 同一APKのinstall `-r`。
- light/dark launch、PID、screenshot、UI XML。
- 通知許可ダイアログが画面を隠していないこと。
- `ACTION_SEND` text。
- `ACTION_PROCESS_TEXT`。
- MediaStoreへ作成した実PNG Content URIの `ACTION_SEND image/png`。
- staged payloadとnative eventの正のlog marker。
- HOMEへ移動後のbackground lifecycle。
- crash／ANR／既知のStatusBar、React host、Foreground Service、AEAD回帰signatureの不在。

## 12. Current evidence state

- 基礎実装の過去の緑証跡: commit `57f738fa3d91e6b78c648c6d540cc25d1124a788`, workflow run `30096422731`。
- 上記証跡ではAndroid buildとAPI 35／36 launch・text share・process text・dark modeが成功した。
- その後、Shizuku状態試験、実PNG共有、background lifecycle、P2S error coalescing、配色比試験、生成工程統合を追加した。
- 現在のHEADは最新CIで再検証中。最終APK authorityは、HEADのbuildとAPI 35／36 smokeが全て成功したrunへ更新してから確定する。
- 古いAPKを完成品として再配布しない。

## 13. Real-device acceptance boundary

エミュレータ緑だけで「安定稼働完成」と宣言しない。次は実機／実サーバーで必要。

- HONOR 400 Proで上書きinstall。
- 日本語・英語・簡体字、light/darkの目視。
- Shizuku未導入／停止／起動済み未認可／認可済み／設定保持後停止の全状態。
- 本家サーバーP2Sと本家デスクトップ間の双方向text／image／file。
- P2Pの2台以上、同一鍵、不一致暗号モード、不一致鍵、Peer離脱／再接続。
- 前景、HOME、画面OFF、Doze、ネット切断復帰、process kill、端末再起動。
- Accessibilityコピー信号のGoogle、Chrome、Firefox、各種入力欄での挙動。
- 長時間実行時のbattery、duplicate send、stale Peer、queue残留。

## 14. Immediate continuation procedure

1. `stability-mobile-otp` HEADとDraft PR #2を確認する。
2. 最新 `Android reliability CI` のbuild/API35/API36を確認する。
3. 失敗時は対応artifactのcheckpoint、summary、exit-info、logcat、screen、UI XMLを読む。
4. 原因を純粋関数または再現可能なemulator stepへ落とし、回帰試験を先に追加する。
5. 全緑後、APKを独立検証し、SHA-256・bytes・signer・commit・runを本書、README、TEST_PLAN、PR本文へ記録する。
6. 実機受入が終わるまでDraft PRを完成扱いにしない。

## 15. Definition of done

次を全て満たすまで完成ではない。

- 最新HEADの生成・lint・unit・Jest・APK検証が成功。
- API 35／36の実PNG共有を含むsmokeが成功。
- 固定署名で旧Extended APKへ上書きinstall成功。
- HONOR 400 Proと本家サーバー／本家desktopで双方向text／image／file成功。
- Shizuku一回設定後、Shizuku停止状態で通常運用成功。
- 前景・背景・画面OFF・再接続・process death・再起動の長時間受入成功。
- 日英簡体字とlight/darkの実画面受入成功。
- 自動診断が実際の故障をFAILとして捕捉し、秘密情報なしでコピー可能。
- `HANDOFF.md`、`WORKLOG.md`、`README.md`、`docs/TEST_PLAN.md`、PR本文が同じ証拠を指す。
