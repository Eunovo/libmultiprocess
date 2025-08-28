# Copyright (c) 2025-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

if("@CMAKE_CXX_COMPILER_ID@" STREQUAL "Clang")
  find_program(LLVM_COV_EXECUTABLE llvm-cov REQUIRED)
  set(COV_TOOL "${LLVM_COV_EXECUTABLE} gcov")
else()
  find_program(GCOV_EXECUTABLE gcov REQUIRED)
  set(COV_TOOL "${GCOV_EXECUTABLE}")
endif()

# COV_TOOL is used to replace a placeholder.
configure_file(
  ${CMAKE_CURRENT_LIST_DIR}/cov_tool_wrapper.sh.in ${CMAKE_CURRENT_LIST_DIR}/cov_tool_wrapper.sh
  FILE_PERMISSIONS OWNER_READ OWNER_EXECUTE
                   GROUP_READ GROUP_EXECUTE
                   WORLD_READ
  @ONLY
)

find_program(LCOV_EXECUTABLE lcov REQUIRED)
separate_arguments(LCOV_OPTS)
set(LCOV_COMMAND ${LCOV_EXECUTABLE} --gcov-tool ${CMAKE_CURRENT_LIST_DIR}/cov_tool_wrapper.sh ${LCOV_OPTS})

find_program(GENHTML_EXECUTABLE genhtml REQUIRED)
set(GENHTML_COMMAND ${GENHTML_EXECUTABLE} --show-details ${LCOV_OPTS})

execute_process(
  COMMAND ${LCOV_COMMAND} --capture --initial --directory . --output-file baseline.info
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  COMMAND_ERROR_IS_FATAL ANY
)

execute_process(
  COMMAND ${CMAKE_CTEST_COMMAND} --build-config Coverage
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  COMMAND_ERROR_IS_FATAL ANY
)
execute_process(
  COMMAND ${LCOV_COMMAND} --capture --directory . --test-name test_libmultiprocess --output-file test_libmultiprocess.info
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  COMMAND_ERROR_IS_FATAL ANY
)
execute_process(
  COMMAND ${LCOV_COMMAND} --add-tracefile baseline.info --add-tracefile test_libmultiprocess.info --output-file coverage.info
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  COMMAND_ERROR_IS_FATAL ANY
)
execute_process(
  COMMAND ${GENHTML_COMMAND} coverage.info --output-directory total.coverage
  WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
  COMMAND_ERROR_IS_FATAL ANY
)
