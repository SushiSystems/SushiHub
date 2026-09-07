/** @file ModulesScreen.cpp
 *  @brief Defines the module rows, their presence chip, their detail line and their action.
 *  @author Mustafa Garip
 */

#include "ui/screens/ModulesScreen.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command this screen reads, which is also its key in the workspace. */
constexpr const char* SCREEN = "status";

/** @brief Holds the command that brings an absent module into the workspace. */
constexpr const char* ADD_COMMAND = "add";

/** @brief Holds the command that brings a binary module up to date. */
constexpr const char* UPDATE_COMMAND = "update";

/** @brief Holds the presence a module without a checkout carries. */
constexpr const char* ABSENT = "absent";

/** @brief Holds the presence a module installed as a released binary carries. */
constexpr const char* BINARY = "binary";

/** @brief Holds the presence a module cloned into the workspace carries. */
constexpr const char* CLONED = "cloned";

/** @brief Holds the presence a module linked from outside the workspace carries. */
constexpr const char* LINKED = "linked";

/** @brief Returns the width, in font sizes, the presence chip's square occupies. */
constexpr float CHIP_SQUARE_SIZE_EM = 0.4F;

/** @brief Returns the gap, in font sizes, between the chip's square and its label. */
constexpr float CHIP_LABEL_GAP_EM = 0.5F;

/** @brief Returns @p value's string field named @p key, or an empty string when it is missing. */
std::string string_field(const nlohmann::json& value, const char* key)
{
    const auto found = value.find(key);
    return (found != value.end() && found->is_string()) ? found->get<std::string>()
                                                         : std::string();
}

/** @brief Returns the colour @p presence is drawn in. */
ImVec4 presence_colour(std::string_view presence)
{
    if (presence == CLONED)
    {
        return Theme::ok();
    }
    if (presence == LINKED)
    {
        return Theme::info();
    }
    if (presence == BINARY)
    {
        return Theme::accent();
    }
    return Theme::ink_faint();
}

/** @brief Returns the dimmed detail line a row draws under a module of @p presence. */
std::string detail_line(const nlohmann::json& module, std::string_view presence)
{
    if (presence == ABSENT)
    {
        return "Open source; can be cloned.";
    }
    if (presence == BINARY)
    {
        const std::string version = string_field(module, "version");
        return version.empty() ? "Installed as a release." : "Version " + version + ".";
    }

    const std::string location = string_field(module, "location");
    const std::string state = string_field(module, "state");
    if (location.empty())
    {
        return state;
    }
    return state.empty() ? location : location + " (" + state + ")";
}

}

ModulesScreen::ModulesScreen(Workspace& workspace, FormOpener& forms)
    : workspace_(workspace),
      forms_(forms)
{
}

const char* ModulesScreen::name() const
{
    return "Modules";
}

void ModulesScreen::draw()
{
    CommandRun& run = workspace_.run_for(SCREEN);
    run.poll();
    const RunState& state = run.state();

    if (!state.result.has_value())
    {
        return;
    }

    const nlohmann::json& payload = state.result->payload;
    const auto modules = payload.find("modules");
    if (modules == payload.end() || !modules->is_array())
    {
        return;
    }

    for (const nlohmann::json& module : *modules)
    {
        draw_row(module);
    }

    draw_provision_note(payload);
}

void ModulesScreen::draw_row(const nlohmann::json& module)
{
    const std::string name = string_field(module, "name");
    const std::string presence = string_field(module, "presence");

    ImGui::PushID(name.c_str());

    draw_presence_chip(presence);
    ImGui::SameLine();
    ImGui::TextUnformatted(name.c_str());

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
    ImGui::TextUnformatted(detail_line(module, presence).c_str());
    ImGui::PopStyleColor();

    ImGui::SameLine(ImGui::GetContentRegionAvail().x - ImGui::GetFontSize() * 4.0F);
    draw_row_action(module, presence);

    ImGui::Separator();
    ImGui::PopID();
}

void ModulesScreen::draw_presence_chip(std::string_view presence)
{
    const float font_size = ImGui::GetFontSize();
    const float square = font_size * CHIP_SQUARE_SIZE_EM;
    const float gap = font_size * CHIP_LABEL_GAP_EM;

    const ImVec2 cursor = ImGui::GetCursorScreenPos();
    const ImVec2 chip_min = cursor;
    const ImVec2 chip_max(cursor.x + square + gap * 2.0F, cursor.y + font_size);

    ImDrawList* draw_list = ImGui::GetWindowDrawList();
    draw_list->AddRectFilled(chip_min, chip_max, ImGui::GetColorU32(Theme::panel()),
                             Theme::corner_radius());

    const ImVec2 square_min(cursor.x + gap, cursor.y + (font_size - square) * 0.5F);
    const ImVec2 square_max(square_min.x + square, square_min.y + square);
    draw_list->AddRectFilled(square_min, square_max,
                             ImGui::GetColorU32(presence_colour(presence)),
                             Theme::corner_radius() * 0.5F);

    ImGui::Dummy(ImVec2(chip_max.x - chip_min.x, chip_max.y - chip_min.y));
}

void ModulesScreen::draw_row_action(const nlohmann::json& module, std::string_view presence)
{
    const std::string name = string_field(module, "name");

    if (presence == ABSENT)
    {
        if (ImGui::SmallButton("Clone"))
        {
            forms_.open_form(ADD_COMMAND, {name});
        }
        return;
    }

    if (presence == BINARY)
    {
        if (ImGui::SmallButton("Update"))
        {
            forms_.open_form(UPDATE_COMMAND, {name});
        }
        return;
    }

    if (ImGui::SmallButton("Details"))
    {
        ImGui::OpenPopup("##sushihub_gui_modules_details");
    }
    if (ImGui::BeginPopup("##sushihub_gui_modules_details"))
    {
        ImGui::Text("%s", string_field(module, "name").c_str());
        ImGui::Separator();
        ImGui::Text("Location: %s", string_field(module, "location").c_str());
        ImGui::Text("State: %s", string_field(module, "state").c_str());
        ImGui::Text("Presence: %s", std::string(presence).c_str());
        ImGui::EndPopup();
    }
}

void ModulesScreen::draw_provision_note(const nlohmann::json& payload)
{
    const auto dependencies = payload.find("dependencies");
    if (dependencies == payload.end() || !dependencies->is_object())
    {
        return;
    }

    const auto count = dependencies->find("pending_count");
    const auto size = dependencies->find("pending_size");
    if (count == dependencies->end() || !count->is_number_integer() || count->get<int>() <= 0)
    {
        return;
    }

    const std::string size_text = (size != dependencies->end() && size->is_string())
                                       ? size->get<std::string>()
                                       : std::string("an unknown size");

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::warn());
    ImGui::Text("The next clone would provision %d dependencies (%s). Defer it with "
               "`hub add --skip-install`.",
               count->get<int>(), size_text.c_str());
    ImGui::PopStyleColor();
}

}
}
