# Copyright (c) The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

# Custom test targets for convenience, based on
# https://gitlab.kitware.com/cmake/community/-/wikis/doc/tutorials/EmulateMakeCheck.
#
# CTest already provides a "make test" target, but it just runs existing tests
# that were previously built, without building anything itself. Define "make
# tests" here as a custom target to build all available tests and "make check"
# as a custom target to build and run them.
add_custom_target(mptests)
add_custom_target(mpcheck COMMAND ${CMAKE_CTEST_COMMAND} DEPENDS mptests)

# Only add more convenient tests and check targets if project is being built
# standalone, to prevent clashes with external projects.
if (MP_STANDALONE)
  add_custom_target(tests DEPENDS mptests)
  add_custom_target(check DEPENDS mpcheck)
endif()

set(abs_top_srcdir ${PROJECT_SOURCE_DIR})
set(abs_top_builddir ${PROJECT_BINARY_DIR})
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/mp/test/constants.py.in ${CMAKE_CURRENT_BINARY_DIR}/mp/test/constants.py USE_SOURCE_PERMISSIONS @ONLY)
file(CREATE_LINK ${CMAKE_CURRENT_SOURCE_DIR}/mp/test/test.py ${CMAKE_CURRENT_BINARY_DIR}/mp/test/test.py COPY_ON_ERROR)

if(BUILD_TESTING AND TARGET CapnProto::kj-test)
  set_property(SOURCE ${MP_PROXY_HDRS} PROPERTY GENERATED 1)

  add_executable(mptest
    ${MP_PROXY_HDRS}
    mp/test/foo-types.h
    mp/test/foo.h
    mp/test/test.cpp
  )
  add_executable(mpfoo
    ${MP_PROXY_HDRS}
    mp/test/foo-types.h
    mp/test/foo.h
    mp/test/foo.cpp
  )
  include(${PROJECT_SOURCE_DIR}/cmake/TargetCapnpSources.cmake)
  target_capnp_sources(mptest ${CMAKE_CURRENT_SOURCE_DIR} mp/test/foo.capnp)
  target_include_directories(mptest PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
  target_link_libraries(mptest PRIVATE CapnProto::kj-test)
  target_link_libraries(mptest PRIVATE Threads::Threads)
  target_capnp_sources(mpfoo ${CMAKE_CURRENT_SOURCE_DIR} mp/test/foo.capnp)
  target_include_directories(mpfoo PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
  target_link_libraries(mpfoo PRIVATE CapnProto::kj-test)
  target_link_libraries(mpfoo PRIVATE Threads::Threads)

  add_dependencies(mptests mptest mpfoo)
  add_test(NAME mptest COMMAND mptest)
endif()
