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
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/grid_layout_test.cpp -o dist/grid_layout_test
./dist/grid_layout_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/grid_selector_test.cpp -o dist/grid_selector_test
./dist/grid_selector_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/grid_fallback_test.cpp -o dist/grid_fallback_test
./dist/grid_fallback_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/linked_record_test.cpp -o dist/linked_record_test
./dist/linked_record_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/record_release_test.cpp -o dist/record_release_test
./dist/record_release_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/selector_lifecycle_test.cpp -o dist/selector_lifecycle_test
./dist/selector_lifecycle_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/a5_initialization_test.cpp -o dist/a5_initialization_test
./dist/a5_initialization_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/glyph_preparation_test.cpp -o dist/glyph_preparation_test
./dist/glyph_preparation_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/basic_cell_conversion_test.cpp -o dist/basic_cell_conversion_test
./dist/basic_cell_conversion_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/direct_grid_conversion_test.cpp -o dist/direct_grid_conversion_test
./dist/direct_grid_conversion_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/level_grid_conversion_test.cpp -o dist/level_grid_conversion_test
./dist/level_grid_conversion_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/record_factory_tail_test.cpp -o dist/record_factory_tail_test
./dist/record_factory_tail_test
c++ -std=c++17 -Wall -Wextra -Werror -Iandroid/app/src/main/cpp tests/record_template_factory_test.cpp -o dist/record_template_factory_test
./dist/record_template_factory_test
echo "All local smoke tests passed"
