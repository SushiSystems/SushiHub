/** @file Event.cpp
 *  @brief Defines the reading of one event line against the event schema.
 *  @author Mustafa Garip
 */

#include "contract/Event.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Builds the error for a key that is missing or holds the wrong type. */
ParseError bad_field(const std::string& kind, const char* key, const char* expected)
{
    return ParseError{"event \"" + kind + "\" needs a " + expected + " \"" + key + "\""};
}

/** @brief Reads the string at @p key into @p out and reports whether it was there. */
bool read_string(const nlohmann::json& object, const char* key, std::string& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_string())
    {
        return false;
    }
    out = found->get<std::string>();
    return true;
}

/** @brief Reads the integer at @p key into @p out and reports whether it was there. */
bool read_integer(const nlohmann::json& object, const char* key, int& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_number_integer())
    {
        return false;
    }
    out = found->get<int>();
    return true;
}

/** @brief Reads the number or null at @p key into @p out and reports whether the key was there. */
bool read_optional_number(const nlohmann::json& object, const char* key,
                          std::optional<double>& out)
{
    const auto found = object.find(key);
    if (found == object.end())
    {
        return false;
    }
    if (found->is_null())
    {
        out.reset();
        return true;
    }
    if (!found->is_number())
    {
        return false;
    }
    out = found->get<double>();
    return true;
}

/** @brief Reads the string or null at @p key into @p out and reports whether the key was there. */
bool read_optional_string(const nlohmann::json& object, const char* key,
                          std::optional<std::string>& out)
{
    const auto found = object.find(key);
    if (found == object.end())
    {
        return false;
    }
    if (found->is_null())
    {
        out.reset();
        return true;
    }
    if (!found->is_string())
    {
        return false;
    }
    out = found->get<std::string>();
    return true;
}

/** @brief Reads the array of strings at @p key into @p out and reports whether it was there. */
bool read_string_array(const nlohmann::json& object, const char* key,
                       std::vector<std::string>& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_array())
    {
        return false;
    }

    out.clear();
    out.reserve(found->size());
    for (const nlohmann::json& element : *found)
    {
        if (!element.is_string())
        {
            return false;
        }
        out.push_back(element.get<std::string>());
    }
    return true;
}

/** @brief Reads the array of string arrays at @p key into @p out. */
bool read_rows(const nlohmann::json& object, const char* key,
               std::vector<std::vector<std::string>>& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_array())
    {
        return false;
    }

    out.clear();
    out.reserve(found->size());
    for (const nlohmann::json& row : *found)
    {
        if (!row.is_array())
        {
            return false;
        }

        std::vector<std::string> cells;
        cells.reserve(row.size());
        for (const nlohmann::json& cell : row)
        {
            if (!cell.is_string())
            {
                return false;
            }
            cells.push_back(cell.get<std::string>());
        }
        out.push_back(std::move(cells));
    }
    return true;
}

/** @brief Reports whether @p level is one of the four severities the schema allows. */
bool is_known_level(const std::string& level)
{
    return level == "info" || level == "success" || level == "warn" || level == "error";
}

/** @brief Reads a line event out of @p object. */
std::variant<Event, ParseError> parse_line(const nlohmann::json& object, const std::string& kind)
{
    LineEvent event;
    if (!read_string(object, "level", event.level))
    {
        return bad_field(kind, "level", "string");
    }
    if (!is_known_level(event.level))
    {
        return ParseError{"event \"line\" has an unknown level \"" + event.level + "\""};
    }
    if (!read_string(object, "message", event.message))
    {
        return bad_field(kind, "message", "string");
    }
    return Event(std::move(event));
}

/** @brief Reads a table event out of @p object. */
std::variant<Event, ParseError> parse_table(const nlohmann::json& object, const std::string& kind)
{
    TableEvent event;
    if (!read_string(object, "title", event.title))
    {
        return bad_field(kind, "title", "string");
    }
    if (!read_string_array(object, "columns", event.columns))
    {
        return bad_field(kind, "columns", "array of strings");
    }
    if (!read_rows(object, "rows", event.rows))
    {
        return bad_field(kind, "rows", "array of arrays of strings");
    }
    return Event(std::move(event));
}

/** @brief Reads a progress event out of @p object. */
std::variant<Event, ParseError> parse_progress(const nlohmann::json& object,
                                               const std::string& kind)
{
    ProgressEvent event;
    if (!read_string(object, "label", event.label))
    {
        return bad_field(kind, "label", "string");
    }
    if (!read_integer(object, "index", event.index))
    {
        return bad_field(kind, "index", "integer");
    }
    if (!read_integer(object, "count", event.count))
    {
        return bad_field(kind, "count", "integer");
    }
    if (!read_optional_number(object, "fraction", event.fraction))
    {
        return bad_field(kind, "fraction", "number or null");
    }
    return Event(std::move(event));
}

/** @brief Reads a result event out of @p object. */
std::variant<Event, ParseError> parse_result(const nlohmann::json& object, const std::string& kind)
{
    const auto ok = object.find("ok");
    if (ok == object.end() || !ok->is_boolean())
    {
        return bad_field(kind, "ok", "boolean");
    }

    const auto payload = object.find("payload");
    if (payload == object.end() || !payload->is_object())
    {
        return bad_field(kind, "payload", "object");
    }

    ResultEvent event;
    event.ok = ok->get<bool>();
    event.payload = *payload;
    return Event(std::move(event));
}

/** @brief Reads a prompt event out of @p object. */
std::variant<Event, ParseError> parse_prompt(const nlohmann::json& object, const std::string& kind)
{
    PromptEvent event;
    if (!read_string(object, "id", event.id))
    {
        return bad_field(kind, "id", "string");
    }
    if (!read_string(object, "message", event.message))
    {
        return bad_field(kind, "message", "string");
    }
    if (!read_optional_string(object, "default", event.default_answer))
    {
        return bad_field(kind, "default", "string or null");
    }
    return Event(std::move(event));
}

}

std::variant<Event, ParseError> parse_event(std::string_view line)
{
    const nlohmann::json object = nlohmann::json::parse(line.begin(), line.end(), nullptr, false);
    if (object.is_discarded())
    {
        return ParseError{"the line is not JSON"};
    }
    if (!object.is_object())
    {
        return ParseError{"the line is not a JSON object"};
    }

    std::string kind;
    if (!read_string(object, "event", kind))
    {
        return ParseError{"the object has no string \"event\" key"};
    }

    if (kind == "line")
    {
        return parse_line(object, kind);
    }
    if (kind == "command")
    {
        CommandEvent event;
        if (!read_string(object, "command", event.command))
        {
            return bad_field(kind, "command", "string");
        }
        return Event(std::move(event));
    }
    if (kind == "header")
    {
        HeaderEvent event;
        if (!read_string(object, "title", event.title))
        {
            return bad_field(kind, "title", "string");
        }
        return Event(std::move(event));
    }
    if (kind == "panel")
    {
        PanelEvent event;
        if (!read_string(object, "title", event.title))
        {
            return bad_field(kind, "title", "string");
        }
        if (!read_string(object, "body", event.body))
        {
            return bad_field(kind, "body", "string");
        }
        return Event(std::move(event));
    }
    if (kind == "table")
    {
        return parse_table(object, kind);
    }
    if (kind == "progress")
    {
        return parse_progress(object, kind);
    }
    if (kind == "result")
    {
        return parse_result(object, kind);
    }
    if (kind == "prompt")
    {
        return parse_prompt(object, kind);
    }

    return ParseError{"unknown event kind \"" + kind + "\""};
}

}
}
