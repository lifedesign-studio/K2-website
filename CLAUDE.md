# CLAUDE.md — K2 dentistry サイトの運用メモ

## 依頼の受け方
- 依頼者はサイト担当の先生。役員会の指示をテキスト・写真・フライヤー（画像/PDF）で渡される
- 内容を `data/events.json`・`data/site.json`（お知らせ `news`）に反映し、`python3 build.py` で `docs/` を再生成する
- 日付・曜日・金額・会場・申込/支払いリンクは原文と突き合わせ、読み取りに迷う箇所は推測せず質問する
- **公開（main への push）は先生の確認を得てから**。確認前の変更はブランチかプレビュー画像で見せる

## 変更の手順
1. データを編集 → `python3 build.py`
2. 変更したページをローカルで確認（`cd docs && python3 -m http.server`、Playwright でスクリーンショット）
3. 先生の OK → `data/` `assets/` `docs/` をまとめてコミットして push

## ルール
- リポジトリは Public。名簿・入金・個人の連絡先は絶対に入れない
- `docs/` は生成物。直接編集しない（`build.py` かデータを直す）
- 新しいイベント画像は `assets/events/` に置き、`image` で参照
- 年度切替時：`site.json` の `copyright_year`、お知らせ、ハンズオンページ（`build.py` の `COURSE_*` と本文）を更新
- ハンズオンコースは別会計・別事務局。申込・問い合わせは事務局フォーム（`links.handson_form`）へ
- 独自ドメイン切替時に `docs/CNAME`（site.k2dent.com）を出力するよう build.py を更新する。切替前に CNAME を置かない

## 月次保守（毎月）
- リンク切れ、申込/支払いリンク、終了イベントの表示、年度・フッター、HTTPS を点検
- 修正は案として提示し、承認後に反映
- GA4 レポート：ページビュー推移、人気ページ、流入元、申込ボタンのクリック
