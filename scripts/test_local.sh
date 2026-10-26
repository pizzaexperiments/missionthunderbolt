#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 scripts/check_public_inputs.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
mkdir -p dist
c++ -std=c++17 -Wall -Wextra -Werror android/app/src/main/cpp/game.cpp tests/core_test.cpp -o dist/core_test
./dist/core_test
c++ -std=c++17 -Wall -Wextra -Werror android/app/src/main/cpp/game.cpp android/app/src/main/cpp/api.cpp tests/api_test.cpp -o dist/api_test
./dist/api_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp android/app/src/main/cpp/game.cpp desktop/main.cpp -o dist/mt_desktop_demo
printf 'q\n' | ./dist/mt_desktop_demo >/dev/null
echo "All local smoke tests passed"
