# Triage interpreter: blob chi marshal duoc tren CPython 3.14
for v in 3.9 3.11 3.12 3.14; do
  echo "===== py -$v ====="
  echo 'cdctf{aa}' | py -$v files/low_on_fun.py; echo "exit=$?"
done
