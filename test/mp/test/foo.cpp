#include <mp/test/foo.capnp.h>
#include <mp/test/foo.capnp.proxy.h>
#include <mp/test/foo.h>

#include <fstream>
#include <iostream>
#include <mp/proxy-io.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cstring>

static void LogPrint(bool raise, const std::string& message)
{
    if (raise) throw std::runtime_error(message);
    std::ofstream("debug.log", std::ios_base::app) << message << std::endl;
}

int main(int argc, char** argv)
{
    LogPrint(false, "Creating Unix domain socket...");
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd == -1) {
        LogPrint(true, "Failed to create socket");
        return 1;
    }
    LogPrint(false, "Socket created successfully, fd=" + std::to_string(fd));

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, "foo.sock", sizeof(addr.sun_path) - 1);

    LogPrint(false, "Removing existing foo.sock file...");
    unlink("foo.sock");

    LogPrint(false, "Binding socket to foo.sock...");
    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
        LogPrint(true, "Failed to bind socket to foo.sock");
        close(fd);
        return 1;
    }
    LogPrint(false, "Socket bound successfully");

    LogPrint(false, "Setting socket to listen mode...");
    if (listen(fd, 5) == -1) {
        LogPrint(true, "Failed to listen on socket");
        close(fd);
        return 1;
    }
    LogPrint(false, "Socket listening successfully");

    LogPrint(false, "Creating EventLoop...");
    mp::EventLoop loop("mpfoo", LogPrint);

    LogPrint(false, "Creating FooImplementation...");
    std::unique_ptr<mp::test::FooImplementation> foo = std::make_unique<mp::test::FooImplementation>();

    LogPrint(false, "Starting Server...");
    mp::ListenConnections<mp::test::messages::FooInterface>(loop, fd, *foo);

    LogPrint(false, "Starting event loop...");
    loop.loop();

    LogPrint(false, "Event loop finished, closing socket...");
    close(fd);
    return 0;
}
