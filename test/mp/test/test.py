#!/usr/bin/env python3
import asyncio
from pathlib import Path
import shutil
import time

from constants import SRC_DIR
from constants import BUILD_DIR
import capnp

def load_capnp_modules():
  if capnp_bin := shutil.which("capnp"):
      # Add the system cap'nproto path so include/capnp/c++.capnp can be found.
      capnp_dir = Path(capnp_bin).parent.parent / "include"
  else:
      # If there is no system cap'nproto, the pycapnp module should have its own "bundled"
      # includes at this location. If pycapnp was installed with bundled capnp,
      # capnp/c++.capnp can be found here.
      capnp_dir = Path(capnp.__path__[0]).parent
  src_dir = Path(SRC_DIR)
  mp_dir = src_dir / "include"
  test_dir = src_dir / "test" / "mp" / "test"
  imports = [str(mp_dir), str(capnp_dir), str(src_dir)]
  return {
      "proxy": capnp.load(str(mp_dir / "mp" / "proxy.capnp"), imports=imports),
      "foo": capnp.load(str(test_dir / "foo.capnp"), imports=imports),
  }

async def make_capnp_foo(capnp_modules, client_end):
  client = capnp.TwoPartyClient(client_end)
  foo = client.bootstrap().cast_as(capnp_modules["foo"].FooInterface)
  threadmap = foo.initThreadMap().threadMap
  thread = threadmap.makeThread('pytest1').result
  ctx = capnp_modules['proxy'].Context()
  ctx.thread = thread
  return ctx, foo

async def main():
  # Start the server in a subprocess
  server_process = await asyncio.create_subprocess_exec(
      str(Path(BUILD_DIR) / "test" / "mpfoo"),
      stdout=None,
      stderr=asyncio.subprocess.PIPE
  )
  print("Started server process with PID", server_process.pid)
  time.sleep(1)  # Give the server a moment to start and create the socket
  socket_path = Path(BUILD_DIR) / "foo.sock"
  if not socket_path.exists():
    raise FileNotFoundError(f"Socket path {socket_path} does not exist. Make sure the 'foo' server is running.")

  client_end = await capnp.AsyncIoStream.create_unix_connection(str(socket_path))
  capnp_modules = load_capnp_modules()
  ctx, foo = await make_capnp_foo(capnp_modules, client_end)

  """
  Make serveral calls to foo that will invoke the callback
   on the client side using the same thread.
  This will force the Waiter to try to post a function while
   the previously posted function is still being executed.
  """

  class CallbackImpl(capnp_modules['foo'].FooCallback.Server):
    async def call(self, context, arg, **kwargs):
      print("CallbackImpl.call", arg)
      return arg + 1
  
    async def destroy(self, context, **kwargs):
      print("CallbackImpl.destroy")
      return

  callback = CallbackImpl()
  for i in range(5):
    foo.callback(ctx, callback, i)

  print(await foo.callback(ctx, callback, i+1))
  client_end.close()
  await server_process.wait()

if __name__ == '__main__':
  asyncio.run(capnp.run(main()))
