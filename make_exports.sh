#!/usr/bin/env bash

find lib -name "*.dll" | while read dll; do \
  out="exports/$(dirname "${dll#lib/}")/$(basename "${dll%.dll}").exports"; \
  mkdir -p "$(dirname "$out")"; \
  objdump -x "$dll" > "$out"; \
done