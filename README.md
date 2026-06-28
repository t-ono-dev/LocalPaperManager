# LocalPaperManager

LocalPaperManagerは、Zoteroの代替として使うことを目的に作成した、ローカル完結型の論文管理ツールです。  
Python + PySide6 + SQLiteで動作し、PDFファイルとBibTeXデータをCドライブ上のローカルフォルダで管理します。

外部クラウドストレージを使わず、PDF本体、文献情報、フォルダ分類、表示設定はすべてローカルに保存されます。

---

## 主な機能

### 論文PDF / BibTeXの取り込み

- PDFファイルのインポート
- BibTeXファイルのインポート
- ウィンドウへのドラッグ&ドロップ取り込み
- PDF取り込み時のDOI自動抽出
- DOIからBibTeXを自動取得し、空欄メタデータを補完
- 取り込み済み論文に対する後からのBibTeX補完

### ローカル論文管理

- SQLiteデータベースによる文献情報管理
- PDFファイルはローカルフォルダ内にコピーして保存
- フォルダ別の論文管理
- 左側にフォルダリストを表示
- 中央に論文リストを表示
- 右側に選択中論文の編集画面を表示

### 論文リスト操作

- Title, Creator, Year, Publication, Journal Abbr, Volume, Pages, DOI, URL, Date Addedなどでソート
- 各コラムの表示 / 非表示切り替え
- 表示設定の保存
- 複数論文の同時選択
- 複数論文の一括削除
- 複数論文の一括フォルダ移動
- Deleteキーによる削除
- PDF付き論文はPDFアイコンで表示
- PDF付き論文のダブルクリックで外部PDFビューアを起動
- URLクリックでブラウザを起動

### メタデータ編集

- 右側の編集欄から各項目を直接編集
- Saveボタンなしで自動保存
- Enterキーで変更を保存
- 複数行欄はCtrl + Enterで保存
- DOI入力時にURLを自動生成
- Publication入力時にJournal Abbrを自動補完

### 参考文献出力

- 単一論文のAPS形式参考文献をクリップボードにコピー
- フォルダ内論文のAPS形式参考文献リストをクリップボードにコピー
- 複数選択した論文のAPS形式参考文献をまとめてコピー
- Volumeはリッチテキスト対応アプリでは太字で貼り付け可能

出力例：

```text
H. Yoshioka, T. Nakamura, and T. Kimoto, “Characterization of very fast states in the vicinity of the conduction band edge at the SiO2/SiC interface by low temperature conductance measurements”, J. Appl. Phys. 115, 014502 (2014).
```

WordやGoogle Docsなどのリッチテキスト対応アプリに貼り付けた場合、Volume部分は太字になります。

---

## 動作環境

- Windows 10 / Windows 11
- Python 3.10以上
- 推奨：Python 3.11 または 3.12
- インターネット接続
  - PDF取り込み時や手動操作でDOIからBibTeXを取得する場合のみ必要です。
  - PDFやデータベースをクラウドへ保存する機能はありません。

---

## 使用ライブラリ

```text
PySide6
bibtexparser
pypdf
```

Pythonパッケージは `requirements.txt` からインストールできます。

---

## フォルダ構成

配布zipには、論文PDF、SQLiteデータベース、個人設定ファイルは含めていません。  
`data/` と `library/` はアプリ実行時またはPDF取り込み時に作成されます。

```text
LocalPaperManager/
├─ app.py
├─ database.py
├─ pdf_utils.py
├─ bibtex_importer.py
├─ metadata_fetcher.py
├─ bibliography.py
├─ journal_abbr.py
├─ requirements.txt
├─ run_app.bat
├─ setup_first_time.bat
├─ create_desktop_shortcut.ps1
├─ resources/
│  ├─ app_icon.ico
│  ├─ app_icon.png
│  ├─ pdf_icon.png
│  └─ local_paper_manager_generated_icon_full.png
├─ data/              # 実行時に作成
│  ├─ papers.db
│  └─ settings.json
└─ library/           # PDF取り込み時に作成
   └─ PDFs/
```

---

## 初回セットアップ

展開したフォルダ内で、以下をダブルクリックします。

```text
setup_first_time.bat
```

このスクリプトにより、以下が自動で実行されます。

1. `.venv` 仮想環境の作成
2. 必要パッケージのインストール
3. デスクトップショートカットの作成

完了後、デスクトップに以下のショートカットが作成されます。

```text
LocalPaperManager
```

以後は、このショートカットをダブルクリックするだけで起動できます。

---

## デスクトップアイコンについて

Windowsのショートカットでは、透明背景付きアイコンが黒塗りに見えることがあります。  
本配布版では、デスクトップショートカット用の `app_icon.ico` は透過背景で作成しています。アイコンは透過背景のまま、キャンバス内で大きめに表示されるよう調整しています。

既に古いショートカットを作成済みの場合は、古いショートカットを削除してから、以下をもう一度実行してください。

```text
setup_first_time.bat
```

または、以下を右クリックしてPowerShellで実行してください。

```text
create_desktop_shortcut.ps1
```

---

## 手動セットアップ

VSCodeやPowerShellから手動で実行する場合は、以下を実行してください。

```powershell
cd LocalPaperManager

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python app.py
```

PowerShellの実行ポリシーでactivateできない場合は、activateせずに以下でも実行できます。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

---

## 起動方法

### デスクトップショートカットから起動

初回セットアップ後は、デスクトップの

```text
LocalPaperManager
```

をダブルクリックして起動します。

### batファイルから起動

アプリフォルダ内の以下をダブルクリックしても起動できます。

```text
run_app.bat
```

### Pythonから起動

```powershell
python app.py
```

または

```powershell
.\.venv\Scripts\python.exe app.py
```

---

## 基本的な使い方

### PDFを取り込む

1. アプリを起動します。
2. PDFファイルをウィンドウにドラッグ&ドロップします。
3. または上部の `Import PDF` をクリックします。
4. PDFからDOIが見つかった場合、BibTeXを自動取得してメタデータを補完します。

PDFは以下にコピーされます。

```text
library/PDFs/
```

### BibTeXを取り込む

1. `.bib` ファイルをウィンドウにドラッグ&ドロップします。
2. または上部の `Import BibTeX` をクリックします。
3. BibTeXの各エントリが文献リストに追加されます。

### 後からBibTeX情報を取得する

DOIが登録されている論文を選択して、以下を実行します。

```text
Fetch BibTeX by DOI
```

この操作はツールバーまたは右クリックメニューから実行できます。  
複数選択にも対応しています。

---

## フォルダ管理

左側のフォルダリストで論文を分類できます。

### フォルダ作成

ツールバーの

```text
New Folder
```

をクリックします。

またはフォルダリストを右クリックして

```text
New Folder
```

を選択します。

### フォルダ名変更

フォルダを右クリックして

```text
Rename Folder
```

を選択します。

### フォルダ削除

フォルダを右クリックして

```text
Delete Folder
```

を選択します。

フォルダを削除しても、論文本体やPDFファイルは削除されません。  
フォルダとの対応だけが削除されます。

---

## 論文の移動・削除

### フォルダ移動

論文を選択して右クリックし、

```text
Move to Folder
```

から移動先フォルダを選択します。

複数論文を選択した状態でも一括移動できます。

### 現在のフォルダから外す

フォルダ表示中に論文を右クリックし、

```text
Remove from Current Folder
```

を選択します。

### ライブラリから削除

論文を選択して右クリックし、

```text
Delete Paper from Library
```

を選択します。

または、論文リストで論文を選択した状態で

```text
Delete
```

キーを押します。

削除されるのはSQLiteデータベース上の文献情報です。  
PDFファイル本体は誤削除防止のため削除されません。

---

## メタデータ編集

論文を1件選択すると、右側に編集欄が表示されます。

編集できる主な項目：

```text
Title
Creators
Year
Date
Publication
Journal Abbr
Volume
Pages
Issue / Number
DOI
URL
BibTeX Key
PDF Path
Notes
```

### 保存方法

- 1行入力欄：Enterキーで保存
- 複数行入力欄：Ctrl + Enterで保存
- フォーカスを外したときも自動保存

### DOIからURLを自動生成

DOI欄に以下のように入力すると、

```text
10.1063/1.4890966
```

URL欄に以下が自動入力されます。

```text
https://doi.org/10.1063/1.4890966
```

### PublicationからJournal Abbrを自動補完

Publication欄に以下のように入力すると、

```text
Journal of Applied Physics
```

Journal Abbr欄に以下が自動入力されます。

```text
J. Appl. Phys.
```

---

## PDFを開く

PDFが登録されている論文には、PDF欄にPDFアイコンが表示されます。

論文行をダブルクリックすると、Windowsで既定に設定されている外部PDFビューアでPDFを開きます。

---

## URLを開く

URLコラムをクリックすると、既定のブラウザでWebページを開きます。

右側編集欄のURLは、以下の操作で開けます。

```text
Ctrl + click
```

または

```text
Double click
```

通常クリックは編集用に残しています。

---

## コラム表示設定

上部メニューの

```text
Columns
```

から、各コラムの表示 / 非表示を切り替えられます。

表ヘッダーを右クリックしても表示 / 非表示を切り替えられます。

表示設定は以下に保存されます。

```text
data/settings.json
```

---

## APS形式参考文献のコピー

### 単一論文

論文を右クリックして、

```text
Copy APS Reference
```

を選択します。

### 複数論文

複数論文を選択して右クリックし、

```text
Copy APS References
```

を選択します。

### フォルダ内の全論文

左側のフォルダを右クリックして、

```text
Copy APS Reference List
```

を選択します。

参考文献リストがクリップボードにコピーされます。

---

## データ保存場所

文献情報はSQLiteデータベースに保存されます。

```text
data/papers.db
```

PDFファイルは以下にコピーされます。

```text
library/PDFs/
```

アプリの表示設定は以下に保存されます。

```text
data/settings.json
```

---

## バックアップ

バックアップする場合は、以下の2つをコピーしてください。

```text
data/papers.db
library/PDFs/
```

必要に応じて表示設定も保存する場合は、以下もコピーします。

```text
data/settings.json
```

---

## 旧バージョンからの移行

旧バージョンから移行する場合は、旧フォルダから以下をコピーします。

```text
旧LocalPaperManager/data/papers.db
旧LocalPaperManager/library/PDFs/
```

コピー先：

```text
新LocalPaperManager/data/papers.db
新LocalPaperManager/library/PDFs/
```

新バージョンを起動すると、不足しているDB列やテーブルは自動で追加されます。

---

## 配布zipに含めないもの

著作権・個人データ保護のため、配布zipには以下を含めません。

```text
data/
library/
.venv/
*.db
*.sqlite
*.pdf
```

実際の論文PDFや個人の文献データベースは、各自のローカル環境で管理してください。

---

## トラブルシューティング

### PySide6がインストールできない

Pythonのバージョンが古い可能性があります。

確認：

```powershell
python --version
py --list
```

Python 3.10以上を使用してください。  
推奨はPython 3.11または3.12です。

### PowerShellでactivateできない

以下のようなエラーが出る場合があります。

```text
このシステムではスクリプトの実行が無効になっているため...
```

その場合はactivateせずに直接実行できます。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

一時的に許可する場合：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### PDFからBibTeXが取得されない

以下を確認してください。

- PDF本文中にDOIが含まれているか
- DOI欄に正しいDOIが入力されているか
- インターネット接続があるか
- DOI resolverがBibTeXを返せる論文か

DOIを手動入力してから、

```text
Fetch BibTeX by DOI
```

を実行してください。

### PDFをダブルクリックしても開かない

以下を確認してください。

- PDF Pathが正しいか
- PDFファイルが実際に存在するか
- WindowsでPDFビューアが既定アプリに設定されているか

### 参考文献のVolumeが太字にならない

貼り付け先がプレーンテキストのみ対応の場合、太字は反映されません。

太字が反映される貼り付け先の例：

- Microsoft Word
- Google Docs
- PowerPoint
- Outlookなどのリッチテキスト対応エディタ

メモ帳や一部のテキストエディタでは通常文字になります。

---

## 設計上の注意

- PDFファイル本体は削除操作では削除しません。
- ライブラリからの削除は、DB上の文献情報のみ削除します。
- DOIからBibTeXを取得する機能ではインターネット接続を使用します。
- 外部クラウドストレージへの保存機能はありません。
- BibTeX取得結果は出版社やDOI resolver側のデータに依存します。
- Journal Abbrの自動補完は完全ではありません。必要に応じて手動修正してください。

---

## ライセンス

個人利用・研究用途を想定したローカルツールです。  
配布や公開を行う場合は、使用ライブラリのライセンスも確認してください。

---

## 開発メモ

本ツールは以下の方針で作成されています。

```text
PDF本体:
    library/PDFs/ に保存

文献情報:
    SQLite database data/papers.db に保存

プロジェクト・フォルダ:
    SQLite上の分類情報として管理

参考文献出力:
    DB内のメタデータからAPS形式テキストを生成

外部サービス:
    DOIからBibTeXを取得する場合のみdoi.orgへアクセス
```
