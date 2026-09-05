/** @file EventLog.cpp
 *  @brief Defines how each event kind reads in the log and how the log follows its tail.
 *  @author Mustafa Garip
 */

#include "ui/widgets/EventLog.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/TableView.hpp"

#include <imgui.h>

#include <string>
#include <variant>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Draws @p message in the colour @p level gives it, wrapped to the region. */
void draw_message(const std::string& level, const std::string& message)
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour(level));
    ImGui::TextWrapped("%s", message.c_str());
    ImGui::PopStyleColor();
}

/** @brief Draws the command line a run announced, marked as the shell would show it. */
void draw_command(const CommandEvent& command)
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextWrapped("$ %s", command.command.c_str());
    ImGui::PopStyleColor();
}

/** @brief Draws a titled block of text as a framed, wrapped paragraph. */
void draw_panel(const PanelEvent& panel)
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText(panel.title.c_str());
    ImGui::PopStyleColor();
    ImGui::TextWrapped("%s", panel.body.c_str());
}

/** @brief Draws the outcome the run ended with as one line. */
void draw_result(const ResultEvent& result)
{
    draw_message(result.ok ? "success" : "error",
                 result.ok ? "The command finished." : "The command failed.");
}

/** @brief Draws whichever kind @p event holds, skipping the progress kind. */
void draw_event(const Event& event, int identifier)
{
    if (const LineEvent* line = std::get_if<LineEvent>(&event))
    {
        draw_message(line->level, line->message);
    }
    else if (const CommandEvent* command = std::get_if<CommandEvent>(&event))
    {
        draw_command(*command);
    }
    else if (const HeaderEvent* header = std::get_if<HeaderEvent>(&event))
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
        ImGui::SeparatorText(header->title.c_str());
        ImGui::PopStyleColor();
    }
    else if (const PanelEvent* panel = std::get_if<PanelEvent>(&event))
    {
        draw_panel(*panel);
    }
    else if (const TableEvent* table = std::get_if<TableEvent>(&event))
    {
        const std::string id = "##event_table_" + std::to_string(identifier);
        draw_table(id.c_str(), *table);
    }
    else if (const PromptEvent* prompt = std::get_if<PromptEvent>(&event))
    {
        draw_message("warn", prompt->message);
    }
    else if (const ResultEvent* result = std::get_if<ResultEvent>(&event))
    {
        draw_result(*result);
    }
}

}

void draw_event_log(const char* id, const RunState& state, float height)
{
    if (!ImGui::BeginChild(id, ImVec2(0.0F, height), ImGuiChildFlags_Borders))
    {
        ImGui::EndChild();
        return;
    }

    const bool follow_tail = ImGui::GetScrollY() >= ImGui::GetScrollMaxY();

    int identifier = 0;
    for (const Event& event : state.events)
    {
        draw_event(event, identifier++);
    }
    for (const ParseError& error : state.errors)
    {
        draw_message("error", "unreadable line: " + error.reason);
    }

    if (follow_tail)
    {
        ImGui::SetScrollHereY(1.0F);
    }
    ImGui::EndChild();
}

}
}
}
