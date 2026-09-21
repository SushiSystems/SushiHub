/** @file Process.cpp
 *  @brief Defines the Windows and POSIX spawn, the reader thread and the line splitting.
 *  @author Mustafa Garip
 */

#include "bridge/Process.hpp"

#include <array>
#include <utility>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <cerrno>
#include <spawn.h>
#include <sys/wait.h>
#include <unistd.h>
extern char** environ;
#endif

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the byte count one read from the child's stdout asks for. */
constexpr std::size_t READ_CHUNK = 4096;

}

#ifdef _WIN32

/** @brief Holds the child's handle and the two pipe ends this side keeps. */
struct Process::Native
{
    /** @brief Holds the child process handle. */
    HANDLE process = nullptr;

    /** @brief Holds the write end of the child's stdin pipe. */
    HANDLE standard_input = nullptr;

    /** @brief Holds the read end of the child's stdout pipe. */
    HANDLE standard_output = nullptr;

    /** @brief Closes every handle the spawn opened. */
    ~Native()
    {
        if (standard_input != nullptr)
        {
            CloseHandle(standard_input);
        }
        if (standard_output != nullptr)
        {
            CloseHandle(standard_output);
        }
        if (process != nullptr)
        {
            CloseHandle(process);
        }
    }
};

namespace
{

/** @brief Converts UTF-8 @p text to the wide string the Windows spawn takes. */
std::wstring widen(const std::string& text)
{
    if (text.empty())
    {
        return std::wstring();
    }

    const int length = MultiByteToWideChar(CP_UTF8, 0, text.data(),
                                           static_cast<int>(text.size()), nullptr, 0);
    if (length <= 0)
    {
        return std::wstring();
    }

    std::wstring wide(static_cast<std::size_t>(length), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.data(), static_cast<int>(text.size()),
                        wide.data(), length);
    return wide;
}

/** @brief Appends @p argument to @p line quoted the way CommandLineToArgvW reads it back. */
void append_quoted(std::wstring& line, const std::wstring& argument)
{
    const bool needs_quotes = argument.empty() ||
                              argument.find_first_of(L" \t\n\v\"") != std::wstring::npos;
    if (!needs_quotes)
    {
        line += argument;
        return;
    }

    line += L'"';
    for (std::size_t index = 0; index < argument.size(); ++index)
    {
        std::size_t backslashes = 0;
        while (index < argument.size() && argument[index] == L'\\')
        {
            ++backslashes;
            ++index;
        }

        if (index == argument.size())
        {
            line.append(backslashes * 2, L'\\');
            break;
        }

        if (argument[index] == L'"')
        {
            line.append(backslashes * 2 + 1, L'\\');
        }
        else
        {
            line.append(backslashes, L'\\');
        }
        line += argument[index];
    }
    line += L'"';
}

/** @brief Builds one command line from @p argv with each element quoted. */
std::wstring build_command_line(const std::vector<std::string>& argv)
{
    std::wstring line;
    for (std::size_t index = 0; index < argv.size(); ++index)
    {
        if (index != 0)
        {
            line += L' ';
        }
        append_quoted(line, widen(argv[index]));
    }
    return line;
}

}

std::unique_ptr<Process> Process::start(const std::vector<std::string>& argv, LineQueue& out)
{
    if (argv.empty())
    {
        return nullptr;
    }

    SECURITY_ATTRIBUTES inheritable{};
    inheritable.nLength = sizeof(inheritable);
    inheritable.bInheritHandle = TRUE;

    HANDLE input_read = nullptr;
    HANDLE input_write = nullptr;
    HANDLE output_read = nullptr;
    HANDLE output_write = nullptr;

    if (CreatePipe(&input_read, &input_write, &inheritable, 0) == 0)
    {
        return nullptr;
    }
    if (CreatePipe(&output_read, &output_write, &inheritable, 0) == 0)
    {
        CloseHandle(input_read);
        CloseHandle(input_write);
        return nullptr;
    }

    SetHandleInformation(input_write, HANDLE_FLAG_INHERIT, 0);
    SetHandleInformation(output_read, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = input_read;
    startup.hStdOutput = output_write;
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);

    std::wstring command_line = build_command_line(argv);
    PROCESS_INFORMATION information{};
    const BOOL spawned = CreateProcessW(nullptr, command_line.data(), nullptr, nullptr, TRUE,
                                        CREATE_NO_WINDOW, nullptr, nullptr, &startup,
                                        &information);

    CloseHandle(input_read);
    CloseHandle(output_write);

    if (spawned == 0)
    {
        CloseHandle(input_write);
        CloseHandle(output_read);
        return nullptr;
    }

    CloseHandle(information.hThread);

    auto native = std::unique_ptr<Native>(new Native());
    native->process = information.hProcess;
    native->standard_input = input_write;
    native->standard_output = output_read;

    return std::unique_ptr<Process>(new Process(std::move(native), out));
}

void Process::write_line(std::string_view line)
{
    if (native_->standard_input == nullptr)
    {
        return;
    }

    std::string payload(line);
    payload += '\n';

    std::size_t written_total = 0;
    while (written_total < payload.size())
    {
        DWORD written = 0;
        const BOOL ok = WriteFile(native_->standard_input, payload.data() + written_total,
                                  static_cast<DWORD>(payload.size() - written_total),
                                  &written, nullptr);
        if (ok == 0 || written == 0)
        {
            return;
        }
        written_total += written;
    }
}

void Process::close_input()
{
    if (native_->standard_input != nullptr)
    {
        CloseHandle(native_->standard_input);
        native_->standard_input = nullptr;
    }
}

bool Process::running() const
{
    {
        const std::lock_guard<std::mutex> guard(state_mutex_);
        if (exited_)
        {
            return false;
        }
    }

    return WaitForSingleObject(native_->process, 0) == WAIT_TIMEOUT;
}

int Process::exit_code()
{
    if (reader_.joinable())
    {
        reader_.join();
    }

    {
        const std::lock_guard<std::mutex> guard(state_mutex_);
        if (exited_)
        {
            lines_.close();
            return exit_code_;
        }
    }

    WaitForSingleObject(native_->process, INFINITE);
    DWORD code = 0;
    GetExitCodeProcess(native_->process, &code);
    remember_exit(static_cast<int>(code));
    lines_.close();

    const std::lock_guard<std::mutex> guard(state_mutex_);
    return exit_code_;
}

void Process::read_until_end()
{
    std::string pending;
    std::array<char, READ_CHUNK> buffer{};

    for (;;)
    {
        DWORD read_bytes = 0;
        const BOOL ok = ReadFile(native_->standard_output, buffer.data(),
                                 static_cast<DWORD>(buffer.size()), &read_bytes, nullptr);
        if (ok == 0 || read_bytes == 0)
        {
            break;
        }
        pending.append(buffer.data(), read_bytes);
        emit_complete_lines(pending);
    }

    flush_pending(pending);
}

#else

/** @brief Holds the child's identifier and the two pipe ends this side keeps. */
struct Process::Native
{
    /** @brief Holds the child process identifier. */
    pid_t pid = -1;

    /** @brief Holds the write end of the child's stdin pipe. */
    int standard_input = -1;

    /** @brief Holds the read end of the child's stdout pipe. */
    int standard_output = -1;

    /** @brief Closes both pipe ends the spawn left open. */
    ~Native()
    {
        if (standard_input >= 0)
        {
            ::close(standard_input);
        }
        if (standard_output >= 0)
        {
            ::close(standard_output);
        }
    }
};

std::unique_ptr<Process> Process::start(const std::vector<std::string>& argv, LineQueue& out)
{
    if (argv.empty())
    {
        return nullptr;
    }

    int input_pipe[2] = {-1, -1};
    int output_pipe[2] = {-1, -1};
    if (::pipe(input_pipe) != 0)
    {
        return nullptr;
    }
    if (::pipe(output_pipe) != 0)
    {
        ::close(input_pipe[0]);
        ::close(input_pipe[1]);
        return nullptr;
    }

    posix_spawn_file_actions_t actions;
    posix_spawn_file_actions_init(&actions);
    posix_spawn_file_actions_adddup2(&actions, input_pipe[0], STDIN_FILENO);
    posix_spawn_file_actions_adddup2(&actions, output_pipe[1], STDOUT_FILENO);
    posix_spawn_file_actions_addclose(&actions, input_pipe[1]);
    posix_spawn_file_actions_addclose(&actions, output_pipe[0]);

    std::vector<char*> arguments;
    arguments.reserve(argv.size() + 1);
    for (const std::string& argument : argv)
    {
        arguments.push_back(const_cast<char*>(argument.c_str()));
    }
    arguments.push_back(nullptr);

    pid_t pid = -1;
    const int spawned = posix_spawnp(&pid, argv.front().c_str(), &actions, nullptr,
                                     arguments.data(), environ);
    posix_spawn_file_actions_destroy(&actions);

    ::close(input_pipe[0]);
    ::close(output_pipe[1]);

    if (spawned != 0)
    {
        ::close(input_pipe[1]);
        ::close(output_pipe[0]);
        return nullptr;
    }

    auto native = std::unique_ptr<Native>(new Native());
    native->pid = pid;
    native->standard_input = input_pipe[1];
    native->standard_output = output_pipe[0];

    return std::unique_ptr<Process>(new Process(std::move(native), out));
}

void Process::write_line(std::string_view line)
{
    if (native_->standard_input < 0)
    {
        return;
    }

    std::string payload(line);
    payload += '\n';

    std::size_t written_total = 0;
    while (written_total < payload.size())
    {
        const ssize_t written = ::write(native_->standard_input, payload.data() + written_total,
                                        payload.size() - written_total);
        if (written < 0)
        {
            if (errno == EINTR)
            {
                continue;
            }
            return;
        }
        written_total += static_cast<std::size_t>(written);
    }
}

void Process::close_input()
{
    if (native_->standard_input >= 0)
    {
        ::close(native_->standard_input);
        native_->standard_input = -1;
    }
}

bool Process::running() const
{
    {
        const std::lock_guard<std::mutex> guard(state_mutex_);
        if (exited_)
        {
            return false;
        }
    }

    int status = 0;
    const pid_t waited = ::waitpid(native_->pid, &status, WNOHANG);
    if (waited != native_->pid)
    {
        return waited == 0;
    }

    remember_exit(WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    return false;
}

int Process::exit_code()
{
    if (reader_.joinable())
    {
        reader_.join();
    }

    {
        const std::lock_guard<std::mutex> guard(state_mutex_);
        if (exited_)
        {
            lines_.close();
            return exit_code_;
        }
    }

    int status = 0;
    while (::waitpid(native_->pid, &status, 0) < 0 && errno == EINTR)
    {
    }
    remember_exit(WIFEXITED(status) ? WEXITSTATUS(status) : -1);
    lines_.close();

    const std::lock_guard<std::mutex> guard(state_mutex_);
    return exit_code_;
}

void Process::read_until_end()
{
    std::string pending;
    std::array<char, READ_CHUNK> buffer{};

    for (;;)
    {
        const ssize_t read_bytes = ::read(native_->standard_output, buffer.data(), buffer.size());
        if (read_bytes < 0 && errno == EINTR)
        {
            continue;
        }
        if (read_bytes <= 0)
        {
            break;
        }
        pending.append(buffer.data(), static_cast<std::size_t>(read_bytes));
        emit_complete_lines(pending);
    }

    flush_pending(pending);
}

#endif

Process::Process(std::unique_ptr<Native> native, LineQueue& out)
    : native_(std::move(native)),
      lines_(out)
{
    reader_ = std::thread(&Process::read_until_end, this);
}

Process::~Process()
{
    close_input();
    exit_code();
}

void Process::remember_exit(int code) const
{
    const std::lock_guard<std::mutex> guard(state_mutex_);
    if (!exited_)
    {
        exited_ = true;
        exit_code_ = code;
    }
}

void Process::emit_complete_lines(std::string& pending)
{
    std::size_t start = 0;
    for (;;)
    {
        const std::size_t newline = pending.find('\n', start);
        if (newline == std::string::npos)
        {
            break;
        }

        std::size_t end = newline;
        if (end > start && pending[end - 1] == '\r')
        {
            --end;
        }
        lines_.push(pending.substr(start, end - start));
        start = newline + 1;
    }

    pending.erase(0, start);
}

void Process::flush_pending(std::string& pending)
{
    if (!pending.empty())
    {
        if (pending.back() == '\r')
        {
            pending.pop_back();
        }
        lines_.push(std::move(pending));
    }
    lines_.close();
}

}
}
