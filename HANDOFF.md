# ClipCascade Extended — 正本引継ぎ

Last updated: **2026-07-23 JST**

新しいスレッドは、次のリポジトリと本書だけを正本として再開すること。

> https://github.com/GoodLight999/ClipCascade-Extended ←これを引継いで開発して！

## 1. Authority / active work

- Repository: `GoodLight999/ClipCascade-Extended`
- Branch: `stability-mobile-otp`（名称は歴史的事情。現在の最優先は汎用クリップボード同期）
- Draft PR: `#2`
- Protocol/server authority: `Sathvik-Rao/ClipCascade`
- Android behavior reference: `wuxinkami/ClipCascade_go_fork`
- Shizuku API: `RikkaApps/Shizuku-API`
- Guided user-facing Shizuku fork: `thedjchi/Shizuku`
- **永久除外:** `GoodLight999/Trash-ClipCascade`。閲覧・参照・引用・試験・移植・事実抽出を一切しない。

## 2. 非交渉要件

1. Androidの汎用クリップボード同期を、前景・背景・画面OFF・再接続・プロセス死亡・再起動を含めて安定稼働させる。
2. 通常経路はADB不要。Accessibilityのコピー信号と通常のオーバーレイ権限で取得する。
3. Shizukuは一回だけ起動し、権限付与と実状態確認後に停止可能でなければならない。通常ランタイムのShizuku Binder依存は禁止。
4. PC ADBは次善策。表示するのは必要な2コマンドだけで、選択・全文コピー可能にする。
5. テキストコピー、Android共有テキスト、画像クリップボード、画像共有、単一／複数ファイル共有を送信対象とする。
6. 本家サーバー、本家デスクトップ、P2S/STOMP、P2P/WebRTC、暗号化、受信画像／ファイルとの互換性を維持する。
7. UI全体を日本語・英語・簡体字中国語へ統一する。追加部分だけ別言語にしない。ダークモードでも明確なコントラストを確保する。
8. 本家由来の更新告知、更新確認通信、`GITHUB`、`HELP`、`DONATE`、`HOMEPAGE`、旧ADB説明を残さない。
9. Packageは `com.clipcascade.extended`、署名鍵は固定、versionCodeは単調増加として上書き更新を維持する。
10. OTP/SMS/emailは汎用クリップボードの実機受入完了まで延期する。
11. 最終段階で、表示値の羅列ではなく実経路を検査する全自動デバッグを搭載する。
12. `HANDOFF.md` と `WORKLOG.md` を挙動・証拠・受入状態の変更ごとに更新する。

## 3. `.3` は実機不合格・再利用禁止

`3.2.0-extended.3` / versionCode `320003` はCIに成功したが、HONOR 400 Pro実機で次の不具合が確認されたため、完成品・基準APK・受入済みビルドとして扱わない。

- ダークモードで灰色背景に黒字となり、セルフテストが読めない。
- 画面の大半が英語で、追加ボタンだけ日本語という言語混在。
- ログイン前に `GITHUB` / `HELP` / `DONATE`、ログイン後に `HOMEPAGE` が残存。
- 本家の `New version available!` が表示される。
- Shizuku側でExtendedを許可済みでも、アプリがShizuku未起動と誤判定する。
- PC ADBポップアップがコピー不能で、さらに本家由来の旧3コマンド説明が重複。
- アプリ前景でもクリップボード送信・受信が動かない。
- Android共有テキスト、画像クリップボード、画像／ファイル共有が動かない。
- 背景移行時にForeground Service系エラーで停止する。
- `Peers: 21` と `AEADBadTagException` が反復表示される。
- Self-Testは `capture-queued`、pending 0を示す一方、送信キューはcount 0で、イベントが消失していた。

「机上に残っている既知の問題はありません」という旧記述は誤り。削除済みとみなし、以後使用しない。

## 4. `.4` で確定した根本原因と修正

Target: `3.2.0-extended.4`, versionCode `320004`。**現時点では修正・CI中であり、まだ実機合格も最終APK完成も宣言しない。**

### 4.1 イベント消失

- ネイティブ保留イベントを排出した後にJS `onClipboardChange` リスナーを登録していた。
- JSリスナーを先に登録し、その後 `ClipboardListener.startListening()` が配送準備を有効化して永続キューをdrainする順へ修正。
- 能動診断はネイティブ→React専用イベントを実送信し、2秒以内の受信を検査する。

### 4.2 Extended専用UI / ローカライズ

- 本家画面への部分挿入を廃止し、ログイン・詳細設定・同期・端末設定・診断をExtended管理へ変更。
- 本家フッター、Homepage、寄付、更新告知、更新／metadata通信、旧ADB説明を生成物から除去。
- Androidのadaptive colorを使用し、本文・入力・ダイアログをダークモード対応。
- 日英簡体字の同一辞書で画面、接続状態、P2P状態、セルフテスト、全自動診断の見出し／判定／検査名を切替。
- 生JSON、例外名、スタックトレースは診断性のため原文を保持。
- ADBダイアログと診断レポートは選択可能かつ全文コピー可能。

### 4.3 Shizuku

- 瞬間的な `pingBinder()` だけで未起動判定していた経路を廃止。
- Sticky Binder受信、Binder死亡通知、最大8秒の非UI待機を実装。
- 認可後は一時的なnon-daemon AIDL UserServiceでREAD_LOGSとoverlay app-opを適用し、各コマンド終了コードとExtended側の実権限状態を検証。
- UserServiceは終了後削除。通常のコピー／通信経路はShizuku APIを呼ばない。

### 4.4 Android共有・画像クリップボード

- `String` / `text/plain` 限定を廃止し、`CharSequence`、Spanned、`text/html`、MIMEなし `ACTION_SEND`、`ACTION_PROCESS_TEXT` を処理。
- 画像、単一ファイル、複数ファイルを処理。
- 未対応共有は `shared_payload_pending=false` へ戻し、残留自動起動を防止。
- Share URIとクリップボードURIは権限が有効な間に `cache/shared_outbound` へ即時コピーし、Extended FileProvider URIとして送る。
- JSON URI配列、容量上限、失敗時部分削除、期限清掃、短時間URI重複抑止を実装。
- 共有ファイル準備失敗Toastも日英簡体字リソース化。

### 4.5 Foreground Service / `Peers: 21`

- Foreground handler登録とネットワーク実体を単一化し、二重起動要求を抑止。
- 開始停止判定を遅延し得るReact stateではなく永続 `wsIsRunning` から計算。
- 停止待ちを10秒で打ち切り、timeoutを状態・診断へ保存。
- 5秒heartbeatを保存し、要求中に15秒以上途絶えた場合は自動診断FAIL。
- `pollFlagsLoop()` の未監督起動を廃止。ループ例外時はエラー保存、リスナー解放、Service停止、ランタイム・リース解放を必ず実行。
- 本家P2PサーバーのPeer一覧は同一usernameのセッションだけであるため、21 Peerは多重／残留セッションが有力。単一ランタイムと正しい停止で増殖を防ぐ。

### 4.6 P2P暗号互換性

- AEAD復号失敗を部屋全体の致命傷にせず、Peer単位で非互換判定・隔離する。
- 隔離Peerを接続再生成と送信対象から外し、互換Peerとの同期は継続。
- 独自DataChannel制御フレームは禁止。旧本家クライアントがクリップボード本文と誤読するため。
- 独自 `COMPATIBILITY` WebSocket種別も禁止。本家サーバーが転送しないため。
- 互換性情報は、本家サーバーがそのまま転送する `OFFER` / `ANSWER` の任意追加フィールドへ格納。旧クライアントは追加フィールドを無視し、Extended同士は接続前判定する。
- Helloのない旧Peerはunknownとして接続し、最初の実ペイロードの暗号Envelope／復号結果で判定する。

## 5. 全自動デバッグの受入仕様

一タップで次を採取・実行し、PASS／要確認／FAILへ分類し、全文コピー可能にする。

- ネイティブ→Reactイベント実往復。
- JSリスナー登録順とnative delivery ready。
- Accessibility有効状態、最後のコピー信号、取得コーディネーター。
- 前景クリップボード実読取、MIME、URI数。
- 永続ネイティブイベント件数。
- 耐久送信キュー件数・状態・失敗。
- Android共有のpending／staging／cache件数・容量。
- Foreground Service状態、最終エラー、heartbeat鮮度、instance ID、二重起動抑止履歴、loop failure。
- P2P候補／互換／非互換Peer数と最終非互換理由。
- Shizuku Binder/API/UID/認可、READ_LOGS、overlay。
- 再起動receiver状態。
- 生状態JSONとネイティブ検査JSON。

## 6. 自動検査

素材化CIは少なくとも次をAPK組立前に拒否する。

- 本家UI／更新通信／旧ADB説明の再混入。
- JSリスナー登録より先のnative queue drain。
- Shizuku通常ランタイム依存。
- DataChannel上の独自制御フレーム、転送されない独自P2P signaling種別。
- 非互換Peerへの送信。
- Foreground多重ランタイム、未監督poll loop、無期限停止待ち、React state依存toggle。
- `text/plain` / `String` 限定共有、未対応共有のpending残留、英語固定Toast。
- 画像／ファイルURIの非退避、comma split、容量／期限／失敗清掃の欠落。
- 日英簡体字辞書、adaptive color、選択／コピーダイアログ、能動診断の欠落。
- OTP Service／権限／クラスの再混入。

## 7. 現在の証拠境界

- `.3`の過去CI成功は、パッケージング証拠としてのみ履歴保存する。製品受入証拠ではない。
- `.4`は修正・CI中。最新HEADの素材化、ESLint、Jest、Android Lint、Kotlin tests、assemble、署名、Manifest/DEX検査がすべて成功するまでAPKを提出しない。
- CI成功後も、HONOR 400 Proと実サーバーで次を実測するまで「全部直った」と宣言しない。
  - 前景／背景／画面OFFでの双方向テキスト。
  - Android共有テキスト、画像クリップボード、画像／複数ファイル共有。
  - P2S／P2P、本家デスクトップとの相互運用。
  - Shizuku一回設定→完全停止→再試験→Shizukuなし再起動。
  - rapid A→B→C、重複、順序、process kill、reboot、長時間idle/reconnect。
  - typing latency、battery、Foreground Service停止／復旧。
  - `.3`→`.4`同一署名上書き更新と設定保持。

## 8. 直近の継続順

1. 最新HEADのCIを緑にする。失敗ログの該当箇所だけを修正し、検査を弱めない。
2. 生成済み `App.js`、`StartForegroundService.js`、Manifest、Kotlinを直接監査する。
3. HANDOFF / WORKLOG / README / TEST_PLAN / PR本文を最終commit・run・hashへ更新。
4. CI artifactを取得し、APK ZIP、zipalign、v2署名、package/version、Manifest、DEX、SHA-256を独立確認する。
5. `.4`を`.3`へ上書きし、全自動デバッグと実機受入マトリクスを実行する。
6. 不具合時は長文手書き報告を要求せず、コピー可能な全自動診断レポートを主証拠に修正する。
7. 汎用クリップボードが全て緑になるまでOTPへ進まない。

`WORKLOG.md` は時系列証拠、`docs/TEST_PLAN.md` は実行マトリクス。PR #2は実機受入までDraftを維持する。
