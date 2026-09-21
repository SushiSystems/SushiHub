/** @file DeviceGrant.cpp
 *  @brief Defines the payload fields and the message shapes a device grant is recognised by.
 *  @author Mustafa Garip
 */

#include "ui/screens/DeviceGrant.hpp"

#include <cctype>
#include <cstddef>
#include <sstream>
#include <variant>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the shortest run of characters a user code is taken to be. */
constexpr std::size_t SHORTEST_CODE = 6;

/** @brief Holds the longest run of characters a user code is taken to be. */
constexpr std::size_t LONGEST_CODE = 24;

/** @brief Reports whether @p word is spelled the way a user code is. */
bool looks_like_code(const std::string& word)
{
    if (word.size() < SHORTEST_CODE || word.size() > LONGEST_CODE)
    {
        return false;
    }

    bool has_letter = false;
    bool has_digit = false;
    for (const char letter : word)
    {
        const unsigned char character = static_cast<unsigned char>(letter);
        if (std::isupper(character) != 0)
        {
            has_letter = true;
        }
        else if (std::isdigit(character) != 0)
        {
            has_digit = true;
        }
        else if (letter != '-')
        {
            return false;
        }
    }
    return has_letter && has_digit;
}

/** @brief Reports whether @p word is the link a person opens. */
bool looks_like_link(const std::string& word)
{
    return word.rfind("http://", 0) == 0 || word.rfind("https://", 0) == 0;
}

/** @brief Takes the code and the link out of @p text into whichever field is still empty. */
void read_words(const std::string& text, DeviceGrant& grant)
{
    std::istringstream stream(text);
    std::string word;
    while (stream >> word)
    {
        if (grant.verification_uri.empty() && looks_like_link(word))
        {
            grant.verification_uri = word;
        }
        else if (grant.user_code.empty() && looks_like_code(word))
        {
            grant.user_code = word;
        }
    }
}

/** @brief Reads the string at @p key of @p payload into @p out when it holds one. */
void read_field(const nlohmann::json& payload, const char* key, std::string& out)
{
    const auto found = payload.find(key);
    if (found != payload.end() && found->is_string())
    {
        out = found->get<std::string>();
    }
}

}

DeviceGrant read_device_grant(const RunState& state)
{
    DeviceGrant grant;

    if (state.result.has_value() && state.result->payload.is_object())
    {
        read_field(state.result->payload, "user_code", grant.user_code);
        read_field(state.result->payload, "verification_uri", grant.verification_uri);
    }

    for (const Event& event : state.events)
    {
        if (const LineEvent* line = std::get_if<LineEvent>(&event))
        {
            read_words(line->message, grant);
        }
        else if (const PanelEvent* panel = std::get_if<PanelEvent>(&event))
        {
            read_words(panel->body, grant);
        }
    }

    return grant;
}

}
}
