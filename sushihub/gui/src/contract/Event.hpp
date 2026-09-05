/** @file Event.hpp
 *  @brief Declares the eight event kinds one line of `ss --json` output can be.
 *  @author Mustafa Garip
 */

#pragma once

#include <nlohmann/json.hpp>

#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Carries one message and the severity the command gave it. */
struct LineEvent
{
    /** @brief Holds one of info, success, warn or error. */
    std::string level;

    /** @brief Holds the text the command wrote. */
    std::string message;
};

/** @brief Carries a command line the run is about to execute. */
struct CommandEvent
{
    /** @brief Holds the command line as the command would type it. */
    std::string command;
};

/** @brief Carries the title of a new section of output. */
struct HeaderEvent
{
    /** @brief Holds the section title. */
    std::string title;
};

/** @brief Carries a titled block of text, used for failures the command explains at length. */
struct PanelEvent
{
    /** @brief Holds the block title. */
    std::string title;

    /** @brief Holds the block text, which may contain newlines. */
    std::string body;
};

/** @brief Carries a table of strings with its column names. */
struct TableEvent
{
    /** @brief Holds the table title. */
    std::string title;

    /** @brief Holds one name per column, left to right. */
    std::vector<std::string> columns;

    /** @brief Holds one cell per column for each row. */
    std::vector<std::vector<std::string>> rows;
};

/** @brief Carries one step of a long run, its position and its completion when known. */
struct ProgressEvent
{
    /** @brief Holds the name of the step being run. */
    std::string label;

    /** @brief Holds the one-based position of this step. */
    int index = 0;

    /** @brief Holds how many steps the run has in total. */
    int count = 0;

    /** @brief Holds the completed fraction from zero to one, or nothing when unknown. */
    std::optional<double> fraction;
};

/** @brief Carries the run's exit status and whatever the command computed. */
struct ResultEvent
{
    /** @brief Records whether the command succeeded. */
    bool ok = false;

    /** @brief Holds the command's own JSON object, empty when it had nothing to report. */
    nlohmann::json payload;
};

/** @brief Carries a question the run stops on until one line reaches the child's stdin. */
struct PromptEvent
{
    /** @brief Holds the identifier an answer is matched to, counted from one within a run. */
    std::string id;

    /** @brief Holds the question as it would be asked in the terminal. */
    std::string message;

    /** @brief Holds the answer an empty line means, or nothing when there is no default. */
    std::optional<std::string> default_answer;
};

/** @brief Names every shape one event line can take. */
using Event = std::variant<LineEvent, CommandEvent, HeaderEvent, PanelEvent, TableEvent,
                           ProgressEvent, ResultEvent, PromptEvent>;

/** @brief Carries why one line or one catalogue could not be read. */
struct ParseError
{
    /** @brief Holds the reason, phrased for a log the user reads. */
    std::string reason;
};

/**
 * @brief Reads one line of `ss --json` output into the event it describes.
 * @param line One JSON object, without its newline.
 * @return The event, or the reason the line could not be read. Never throws.
 */
std::variant<Event, ParseError> parse_event(std::string_view line);

}
}
