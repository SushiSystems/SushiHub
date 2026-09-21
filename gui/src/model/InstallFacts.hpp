/** @file InstallFacts.hpp
 *  @brief Declares the sentences an install card shows, derived from the status payload.
 *  @author Mustafa Garip
 */

#pragma once

#include <nlohmann/json.hpp>

#include <string>

namespace SushiHub
{
namespace Gui
{
namespace InstallFacts
{

/** @brief Returns the entry of @p payload's module array named @p name, or null when absent. */
const nlohmann::json* find_module(const nlohmann::json& payload, const std::string& name);

/** @brief Returns @p object's string at @p key, or @p fallback when it is null or missing. */
std::string text(const nlohmann::json& object, const char* key, const std::string& fallback);

/** @brief Returns a checkout's distance from upstream, as "+2 / -0" or "no upstream". */
std::string distance(const nlohmann::json& source);

/**
 * @brief Returns how long ago @p source was last fetched, counted in whole days.
 * @param today_days Today as days since 1970-01-01 in UTC.
 */
std::string last_fetch(const nlohmann::json& source, long today_days);

/** @brief Returns what a binary module's licence file says, or that there is none. */
std::string licence(const nlohmann::json& module);

/**
 * @brief Returns whether a newer release of a binary module exists.
 * @param checked Whether the payload came from `hub status --check-updates`.
 */
std::string newer_release(const nlohmann::json& module, bool checked);

/** @brief Returns where the `sh` alias is defined, or that it is not. */
std::string alias(const nlohmann::json& hub);

/**
 * @brief Returns whether the workspace checkout `hub` runs from is current.
 * @param checked Whether the payload came from `hub status --check-updates`.
 */
std::string hub_currency(const nlohmann::json& hub, bool checked);

/** @brief Returns the days since 1970-01-01 of an iso-8601 date's date part, or -1 when unreadable. */
long days_from_iso(const std::string& iso);

/** @brief Returns today as days since 1970-01-01 in UTC. */
long today_days();

}
}
}
