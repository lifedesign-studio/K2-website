# K2 dentistry 公式サイト

歯科スタディグループ K2 のホームページ（公開予定：https://site.k2dent.com ）。

## 仕組み

- `data/site.json` … サイト全体の設定（配色 `theme`：mono / gold / navy、入会フォームなどのリンク、お知らせ、年度、GA4の測定ID）
- `data/events.json` … イベント（定例会・講演会・サマーセミナー・懇親会など）。1件ずつ追加する
- `assets/` … CSS、画像、ファビコン、共有用画像（ogp.png）
- `build.py` … 上のデータから `docs/` にサイトを書き出す（`python3 build.py`）
- `docs/` … 公開されるサイト本体（自動生成。直接編集しない）

GitHub Pages の設定：Settings → Pages → Deploy from a branch → `main` / `/docs`

## イベントの追加

`data/events.json` の `events` に1件追加して `python3 build.py` を実行する。

```json
{
  "id": "2026-11-case-meeting",
  "title": "第3回 症例発表会",
  "type": "定例会",
  "date": "2026-11-15",
  "time": "14:00〜18:00",
  "venue": "会場名",
  "address": "住所",
  "map_url": "https://maps.google.com/...",
  "target": "K2会員、コデンタルスタッフ",
  "fees": [{ "label": "歯科医師（会員）", "amount": "無料" }],
  "deadline": "11月8日（日）",
  "walkin": true,
  "walkin_note": "受付で名簿にご記入ください",
  "summary": "一覧や共有時に表示される1〜2文の説明",
  "body": ["本文の段落1", "本文の段落2"],
  "apply_url": "申込フォームのURL",
  "pay_url": "支払いページのURL",
  "image": "/assets/events/2026-11-flyer.jpg",
  "contact": "担当：〇〇"
}
```

必須は `id`（英数字とハイフン。URLになる）・`title`・`date`。ほかは書いたものだけ表示される。
開催日を過ぎたイベントは自動で「過去の開催」に移る。

## 守ること

- このリポジトリは公開（Public）。**名簿・入金記録・個人の連絡先など個人情報は絶対に入れない**
- 公開前に、日付・金額・会場を担当者が確認する
- ハンズオンコースは事務局・会計がK2と別。申込・問い合わせは事務局の申込フォームへ案内する
