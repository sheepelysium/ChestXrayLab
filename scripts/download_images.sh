#!/usr/bin/env bash
# 從 NIH 官方 Box 下載 12 個影像壓縮檔到 data/raw/archives（可續傳）。
# 用法：bash scripts/download_images.sh <worker 編號 0..N-1> <worker 總數 N>
# 每個 worker 只處理 (檔案編號-1) % N == worker 編號 的檔案，彼此不會寫到同一個檔。
# 連結來自官方 images/batch_download_zips.py；下載後用 scripts/verify_archives.py 核對 MD5。
set -u
worker="${1:-0}"
total="${2:-1}"
dest="$(cd "$(dirname "$0")/.." && pwd)/data/raw/archives"
mkdir -p "$dest"
ids=(
  vfk49d74nhbxq3nqjg0900w5nvkorp5c
  i28rlmbvmfjbl8p2n3ril0pptcmcu9d1
  f1t00wrtdk94satdfb9olcolqx20z2jp
  0aowwzs5lhjrceb3qp67ahp0rd1l1etg
  v5e3goj22zr6h8tzualxfsqlqaygfbsn
  asi7ikud9jwnkrnkj99jnpfkjdes7l6l
  jn1b4mw4n6lnh74ovmcjb8y48h8xj07n
  tvpxmn7qyrgl0w8wfh9kqfjskv6nmm1j
  upyy3ml7qdumlgk2rfcvlb9k6gvqq2pj
  l6nilvfa9cg3s28tqv1qc1olm3gnz54p
  hhq8fkdgvcari67vfhs7ppg2w6ni4jze
  ioqwiy20ihqwyr8pf4c24eazhh281pbu
)
for i in "${!ids[@]}"; do
  if [ $((i % total)) -ne "$worker" ]; then continue; fi
  name=$(printf "images_%03d.tar.gz" $((i + 1)))
  if [ -f "$dest/$name.done" ]; then continue; fi
  if curl -sSL --retry 8 --retry-delay 10 --retry-all-errors -C - \
      -o "$dest/$name" "https://nihcc.box.com/shared/static/${ids[$i]}.gz"; then
    touch "$dest/$name.done"
    echo "$(date +%H:%M:%S) ok $name" >> "$dest/download.log"
  else
    echo "$(date +%H:%M:%S) FAILED $name (curl exit $?)" >> "$dest/download.log"
  fi
done
echo "$(date +%H:%M:%S) worker $worker finished" >> "$dest/download.log"
