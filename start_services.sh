#!/bin/bash
git init
git config --local user.email "fava@homelab"
git config --local user.name "fava"

fava main.bean

wait -n

exit $?