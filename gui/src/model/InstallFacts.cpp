/** @file InstallFacts.cpp
 *  @brief Defines the sentences an install card shows, derived from the status payload.
 *  @author Mustafa Garip
 */

#include "model/InstallFacts.hpp"

#include <chrono>

namespace SushiHub
{
namespace Gui
{
namespace InstallFacts
{

namespace
{

/** @brief Returns @p object's integer at @p key, or -1 when it is null or missing. */
long integer(const nlohmann::json& object, const char* key)
{
    const auto found = object.find(key);
    return found != object.end() && found->is_number_integer() ? found->get<long>() : -1;
}

/** @brief Returns the number @p count digits of @p iso spell from @p at, or -1 on a non-digit. */
long digits(const std::string& iso, std::size_t at, std::size_t count)
{
    long value = 0;
    for (std::size_t index = at; index < at + count; ++index)
    {
        if (index >= iso.size() || iso[index] < '0' || iso[index] > '9')
        {
            return -1;
        }
        value = value * 10 + (iso[index] - '0');
    }
    return value;
}

/** @brief Returns the days since 1970-01-01 of a proleptic Gregorian date. */
long days_from_civil(long year, unsigned month, unsigned day)
{
    // The year is shifted to begin in March, so a leap day is the last day of its year.
    year -= month <= 2 ? 1 : 0;
    const long era = (year >= 0 ? year : year - 399) / 400;
    const unsigned year_of_era = static_cast<unsigned>(year - era * 400);
    const unsigned day_of_year = (153 * (month > 2 ? month - 3 : month + 9) + 2) / 5 + day - 1;
    const unsigned day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 +
                                day_of_year;
    return era * 146097 + static_cast<long>(day_of_era) - 719468;
}

}

const nlohmann::json* find_module(const nlohmann::json& payload, const std::string& name)
{
    const auto modules = payload.find("modules");
    if (modules == payload.end() || !modules->is_array())
    {
        return nullptr;
    }
    for (const nlohmann::json& entry : *modules)
    {
        if (entry.is_object() && entry.value("name", std::string()) == name)
        {
            return &entry;
        }
    }
    return nullptr;
}

std::string text(const nlohmann::json& object, const char* key, const std::string& fallback)
{
    const auto found = object.find(key);
    return found != object.end() && found->is_string() ? found->get<std::string>() : fallback;
}

std::string distance(const nlohmann::json& source)
{
    const long ahead = integer(source, "ahead");
    const long behind = integer(source, "behind");
    if (ahead < 0 || behind < 0)
    {
        return "no upstream";
    }
    return "+" + std::to_string(ahead) + " / -" + std::to_string(behind);
}

std::string last_fetch(const nlohmann::json& source, long today_days)
{
    const long fetched = days_from_iso(text(source, "last_fetch", std::string()));
    if (fetched < 0)
    {
        return "never fetched";
    }
    const long age = today_days - fetched;
    if (age <= 0)
    {
        return "fetched today";
    }
    return "fetched " + std::to_string(age) + (age == 1 ? " day ago" : " days ago");
}

std::string licence(const nlohmann::json& module)
{
    const auto binary = module.find("binary");
    if (binary == module.end() || !binary->is_object())
    {
        return "no licence file";
    }
    const std::string expiry = text(*binary, "licence_expires_at", std::string());
    return expiry.empty() ? "no licence file" : "until " + expiry.substr(0, 10);
}

std::string newer_release(const nlohmann::json& module, bool checked)
{
    if (!checked)
    {
        return "not checked";
    }
    const std::string latest = text(module, "latest_version", std::string());
    if (latest.empty())
    {
        return "could not check";
    }
    return latest == text(module, "version", std::string()) ? "up to date" : latest + " available";
}

std::string alias(const nlohmann::json& hub)
{
    const auto found = hub.find("alias");
    if (found == hub.end() || !found->is_object())
    {
        return "not defined";
    }
    return text(*found, "name", "sh") + ", in " + text(*found, "defined_in", "?");
}

std::string hub_currency(const nlohmann::json& hub, bool checked)
{
    const auto source = hub.find("source");
    if (source == hub.end() || !source->is_object())
    {
        return "unknown";
    }
    const long behind = integer(*source, "behind");
    if (behind < 0)
    {
        return "no upstream";
    }
    if (behind == 0)
    {
        return checked ? "up to date" : "up to date at last fetch";
    }
    return std::to_string(behind) + (behind == 1 ? " commit" : " commits") + " behind";
}

long days_from_iso(const std::string& iso)
{
    const long year = digits(iso, 0, 4);
    const long month = digits(iso, 5, 2);
    const long day = digits(iso, 8, 2);
    if (year < 0 || iso.size() < 10 || iso[4] != '-' || iso[7] != '-' || month < 1 ||
        month > 12 || day < 1 || day > 31)
    {
        return -1;
    }
    return days_from_civil(year, static_cast<unsigned>(month), static_cast<unsigned>(day));
}

long today_days()
{
    const auto now = std::chrono::system_clock::now().time_since_epoch();
    return static_cast<long>(std::chrono::duration_cast<std::chrono::hours>(now).count() / 24);
}

}
}
}
