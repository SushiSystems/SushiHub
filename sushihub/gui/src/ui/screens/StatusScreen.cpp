/** @file StatusScreen.cpp
 *  @brief Defines the status screen's tables, its dependency line and its refresh.
 *  @author Mustafa Garip
 */

#include "ui/screens/StatusScreen.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"
#include "ui/widgets/ProgressBar.hpp"
#include "ui/widgets/TableView.hpp"

#include <imgui.h>

#include <string>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command this screen reads, which is also its key in the workspace. */
constexpr const char* SCREEN = "status";

/** @brief Returns where the dependency tree sits, as @p value spells it. */
std::string dependency_line(const nlohmann::json& value)
{
    if (value.is_string())
    {
        return value.get<std::string>();
    }
    if (!value.is_object())
    {
        return std::string();
    }

    const auto path = value.find("path");
    if (path == value.end() || !path->is_string())
    {
        return std::string();
    }

    const auto present = value.find("present");
    const bool provisioned = present != value.end() && present->is_boolean() &&
                             present->get<bool>();
    return path->get<std::string>() + (provisioned ? " (present)" : " (empty)");
}

}

StatusScreen::StatusScreen(Workspace& workspace)
    : workspace_(workspace)
{
}

void StatusScreen::draw()
{
    CommandRun& run = workspace_.run_for(SCREEN);
    run.poll();
    const RunState& state = run.state();

    const bool refresh = ImGui::Button("Refresh");
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted(state.finished ? "up to date" : "reading the workspace...");
    ImGui::PopStyleColor();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (std::size_t index = 0; index < state.tables.size(); ++index)
    {
        const std::string id = "##sushihub_gui_status_table_" + std::to_string(index);
        Widgets::draw_table(id.c_str(), state.tables[index]);
    }

    draw_dependencies(state);

    if (state.pending_prompt.has_value())
    {
        std::string answer;
        if (prompt_.draw(*state.pending_prompt, answer))
        {
            run.answer_prompt(answer);
        }
    }

    Widgets::draw_event_log("##sushihub_gui_status_log", state, 0.0F);

    if (refresh)
    {
        workspace_.refresh(SCREEN);
    }
}

void StatusScreen::draw_dependencies(const RunState& state)
{
    if (!state.result.has_value())
    {
        return;
    }

    const nlohmann::json& payload = state.result->payload;
    const auto dependencies = payload.find("dependencies");
    if (dependencies == payload.end())
    {
        return;
    }

    const std::string line = dependency_line(*dependencies);
    if (!line.empty())
    {
        ImGui::Text("Dependencies: %s", line.c_str());
    }
}

}
}
