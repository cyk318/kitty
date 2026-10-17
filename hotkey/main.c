// 仅注册 Option+空格；窗口、输入法和显示/隐藏逻辑全部交给 Kitty 原生面板。
#include <Carbon/Carbon.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <unistd.h>

extern char **environ;
static char *kitten_path;

static OSStatus toggle_kitty(EventHandlerCallRef next, EventRef event, void *data) {
    (void)next;
    (void)data;
    EventHotKeyID key;
    OSStatus status = GetEventParameter(event, kEventParamDirectObject,
        typeEventHotKeyID, NULL, sizeof(key), NULL, &key);
    if (status != noErr || key.signature != 'KTTY' || key.id != 1)
        return eventNotHandledErr;

    // 不使用 --detach：直接调用原生单实例切换，首次调用也可以启动面板。
    char *args[] = {kitten_path, "quick-access-terminal", NULL};
    pid_t child;
    posix_spawnattr_t attributes;
    int error = posix_spawnattr_init(&attributes);
    if (error) {
        fprintf(stderr, "Cannot initialize spawn attributes: %d\n", error);
        return noErr;
    }
    // 助手忽略子进程退出信号，但 Kitty 必须使用正常的子进程处理方式。
    sigset_t defaults;
    sigemptyset(&defaults);
    sigaddset(&defaults, SIGCHLD);
    error = posix_spawnattr_setsigdefault(&attributes, &defaults);
    if (!error) error = posix_spawnattr_setflags(&attributes, POSIX_SPAWN_SETSIGDEF);
    if (!error) error = posix_spawn(&child, args[0], NULL, &attributes, args, environ);
    posix_spawnattr_destroy(&attributes);
    if (error) fprintf(stderr, "Cannot launch Kitty: %d\n", error);
    return noErr;
}

int main(int argc, char **argv) {
    // 安装脚本传入本机路径；源码不包含用户名或固定的 Kitty 安装位置。
    if (argc != 2 || access(argv[1], X_OK) != 0) {
        fprintf(stderr, "Usage: kitty-hotkey /absolute/path/to/kitten\n");
        return 1;
    }
    kitten_path = argv[1];
    signal(SIGCHLD, SIG_IGN);
    EventTypeSpec event = {kEventClassKeyboard, kEventHotKeyPressed};
    OSStatus status = InstallApplicationEventHandler(toggle_kitty, 1, &event, NULL, NULL);
    if (status != noErr) {
        fprintf(stderr, "Cannot install hotkey handler: %d\n", (int)status);
        return 1;
    }

    EventHotKeyRef hotkey;
    EventHotKeyID key = {'KTTY', 1};
    status = RegisterEventHotKey(kVK_Space, optionKey, key,
        GetApplicationEventTarget(), 0, &hotkey);
    if (status != noErr) {
        fprintf(stderr, "Cannot register Option+Space: %d\n", (int)status);
        return 2;
    }
    // 阻塞等待系统事件，空闲时不轮询、不记录用户输入。
    EventRef received;
    while (ReceiveNextEvent(0, NULL, kEventDurationForever, true, &received) == noErr) {
        SendEventToEventTarget(received, GetEventDispatcherTarget());
        ReleaseEvent(received);
    }
    UnregisterEventHotKey(hotkey);
    return 0;
}
