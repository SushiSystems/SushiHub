/** @file LineQueue.cpp
 *  @brief Defines the mutex-guarded deque behind LineQueue.
 *  @author Mustafa Garip
 */

#include "bridge/LineQueue.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

void LineQueue::push(std::string line)
{
    const std::lock_guard<std::mutex> guard(mutex_);
    lines_.push_back(std::move(line));
}

bool LineQueue::try_pop(std::string& line)
{
    const std::lock_guard<std::mutex> guard(mutex_);
    if (lines_.empty())
    {
        return false;
    }

    line = std::move(lines_.front());
    lines_.pop_front();
    return true;
}

void LineQueue::close()
{
    const std::lock_guard<std::mutex> guard(mutex_);
    closed_ = true;
}

bool LineQueue::closed() const
{
    const std::lock_guard<std::mutex> guard(mutex_);
    return closed_;
}

bool LineQueue::empty() const
{
    const std::lock_guard<std::mutex> guard(mutex_);
    return lines_.empty();
}

}
}
