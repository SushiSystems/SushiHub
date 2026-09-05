/** @file DeviceGrant.hpp
 *  @brief Declares what a person needs to approve a sign-in and how a run is read for it.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunState.hpp"

#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Holds one sign-in in flight: the code a person types and the page to type it on. */
struct DeviceGrant
{
    /** @brief Holds the code the person types, empty until the run has shown one. */
    std::string user_code;

    /** @brief Holds the page the code is typed on, empty until the run has shown one. */
    std::string verification_uri;
};

/**
 * @brief Reads the grant out of what a sign-in run has produced so far.
 * @param state The run's state; the result payload's own fields win over its messages.
 * @return The code and the page, either field empty when the run has not shown it.
 */
DeviceGrant read_device_grant(const RunState& state);

}
}
