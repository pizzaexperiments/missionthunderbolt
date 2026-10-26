cmake_minimum_required(VERSION 3.22.1)
project(thunderbolt_native LANGUAGES CXX)
add_library(thunderbolt SHARED game.cpp api.cpp bridge.cpp)
target_compile_features(thunderbolt PRIVATE cxx_std_17)
