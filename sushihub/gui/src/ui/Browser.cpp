/** @file Browser.cpp
 *  @brief Defines the Windows shell association and the POSIX opener a link is handed to.
 *  @author Mustafa Garip
 */

#include "ui/Browser.hpp"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <shellapi.h>
#else
#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"

#include <memory>
#endif

namespace SushiHub
{
namespace Gui
{

#ifdef _WIN32

namespace
{

/** @brief Returns @p text as UTF-16, empty when it holds no characters. */
std::wstring widen(const std::string& text)
{
    if (text.empty())
    {
        return std::wstring();
    }

    const int length = MultiByteToWideChar(CP_UTF8, 0, text.data(), static_cast<int>(text.size()),
                                           nullptr, 0);
    if (length <= 0)
    {
        return std::wstring();
    }

    std::wstring wide(static_cast<std::size_t>(length), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.data(), static_cast<int>(text.size()), wide.data(),
                        length);
    return wide;
}

/** @brief Holds the return value above which ShellExecuteW reports success. */
constexpr INT_PTR SHELL_EXECUTE_SUCCESS = 32;

}

bool open_in_browser(const std::string& url)
{
    const std::wstring wide = widen(url);
    if (wide.empty())
    {
        return false;
    }

    const HINSTANCE result = ShellExecuteW(nullptr, L"open", wide.c_str(), nullptr, nullptr,
                                           SW_SHOWNORMAL);
    return reinterpret_cast<INT_PTR>(result) > SHELL_EXECUTE_SUCCESS;
}

#else

namespace
{

/** @brief Holds the last opener spawned, so its child is waited for when the next one starts. */
struct Opener
{
    /** @brief Takes whatever the opener writes and is never drained. */
    LineQueue discarded;

    /** @brief Holds the running opener, null until the first link is opened. */
    std::unique_ptr<Process> process;
};

/** @brief Returns the one opener the process keeps. */
Opener& opener()
{
    static Opener kept;
    return kept;
}

}

bool open_in_browser(const std::string& url)
{
    if (url.empty())
    {
        return false;
    }

    Opener& kept = opener();
    kept.process = Process::start({"xdg-open", url}, kept.discarded);
    return kept.process != nullptr;
}

#endif

}
}
