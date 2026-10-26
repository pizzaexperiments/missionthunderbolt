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
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp android/app/src/main/cpp/game.cpp android/app/src/main/cpp/api.cpp tests/save_test.cpp -o dist/save_test
./dist/save_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp android/app/src/main/cpp/game.cpp android/app/src/main/cpp/api.cpp tests/fuzz_test.cpp -o dist/fuzz_test
./dist/fuzz_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp android/app/src/main/cpp/game.cpp android/app/src/main/cpp/api.cpp tests/manual_rules_test.cpp -o dist/manual_rules_test
./dist/manual_rules_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp android/app/src/main/cpp/game.cpp desktop/main.cpp -o dist/mt_desktop_demo
printf 'q\n' | ./dist/mt_desktop_demo >/dev/null
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/legacy_rng_test.cpp -o dist/legacy_rng_test
./dist/legacy_rng_test
echo "All local smoke tests passed"
