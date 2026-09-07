/** @file InstallsScreen.cpp
 *  @brief Defines the two install cards, their presence chips, their fields and their actions.
 *  @author Mustafa Garip
 */

#include "ui/screens/InstallsScreen.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command this screen reads, which is also its key in the workspace. */
constexpr const char* STATUS_SCREEN = "status";

/** @brief Holds the key of the module array inside the status run's result payload. */
constexpr const char* MODULES_KEY = "modules";

/** @brief Holds the key that names a module within its own entry. */
constexpr const char* NAME_KEY = "name";

/** @brief Holds the key that carries a module's presence within its own entry. */
constexpr const char* PRESENCE_KEY = "presence";

/** @brief Holds the presence a card whose path is a checkout reports. */
constexpr const char* PRESENCE_CLONED = "cloned";

/** @brief Holds the presence a card whose path is a release reports. */
constexpr const char* PRESENCE_BINARY = "binary";

/** @brief Holds the presence a card that has neither path yet reports. */
constexpr const char* PRESENCE_ABSENT = "absent";

/** @brief Holds the program that opens the engine's editor, started outside of `hub`. */
constexpr const char* EDITOR_PROGRAM = "se";

/** @brief Returns the entry of @p payload's module array named @p name, or null when absent. */
const nlohmann::json* find_module(const nlohmann::json& payload, const char* name)
{
    const auto modules = payload.find(MODULES_KEY);
    if (modules == payload.end() || !modules->is_array())
    {
        return nullptr;
    }
    for (const nlohmann::json& entry : *modules)
    {
        if (entry.is_object() && entry.value(NAME_KEY, std::string()) == name)
        {
            return &entry;
        }
    }
    return nullptr;
}

/** @brief Returns @p module's string field @p key, or a dash when it is absent or not a string. */
std::string field(const nlohmann::json& module, const char* key)
{
    const auto found = module.find(key);
    if (found == module.end() || !found->is_string())
    {
        return "-";
    }
    return found->get<std::string>();
}

/** @brief Returns the colour @p presence's chip fills with. */
ImVec4 presence_colour(const std::string& presence)
{
    if (presence == PRESENCE_CLONED || presence == "linked")
    {
        return Theme::ok();
    }
    if (presence == PRESENCE_BINARY)
    {
        return Theme::accent();
    }
    return Theme::ink_faint();
}

}

InstallsScreen::InstallsScreen(Workspace& workspace, RunLog& run_log)
    : workspace_(workspace),
      run_log_(run_log)
{
}

const char* InstallsScreen::name() const
{
    return "Installs";
}

void InstallsScreen::draw()
{
    CommandRun& run = workspace_.run_for(STATUS_SCREEN);
    run.poll();
    const RunState& state = run.state();

    const nlohmann::json* engine = nullptr;
    const nlohmann::json* hub = nullptr;
    if (state.result.has_value())
    {
        engine = find_module(state.result->payload, "sushiengine");
        hub = find_module(state.result->payload, "sushihub");
    }

    draw_engine_card(engine);
    ImGui::Dummy(ImVec2(0.0F, ImGui::GetFontSize() * 0.5F));
    draw_hub_card(hub);
}

void InstallsScreen::draw_title(const char* title, const std::string& presence)
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink());
    ImGui::TextUnformatted(title);
    ImGui::PopStyleColor();

    if (presence.empty())
    {
        return;
    }

    ImGui::SameLine();
    const float side = ImGui::GetFontSize() * 0.4F;
    const ImVec2 origin = ImGui::GetCursorScreenPos();
    const float baseline = ImGui::GetFontSize() * 0.2F;
    ImGui::GetWindowDrawList()->AddRectFilled(
        ImVec2(origin.x, origin.y + baseline), ImVec2(origin.x + side, origin.y + baseline + side),
        ImGui::ColorConvertFloat4ToU32(presence_colour(presence)));
    ImGui::Dummy(ImVec2(side, ImGui::GetFontSize()));
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
    ImGui::TextUnformatted(presence.c_str());
    ImGui::PopStyleColor();
}

void InstallsScreen::draw_fields(const std::vector<std::pair<const char*, std::string>>& fields)
{
    if (!ImGui::BeginTable("##sushihub_gui_installs_fields", static_cast<int>(fields.size())))
    {
        return;
    }
    for (const auto& entry : fields)
    {
        ImGui::TableNextColumn();
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
        ImGui::TextUnformatted(entry.first);
        ImGui::PopStyleColor();
        ImGui::TextUnformatted(entry.second.c_str());
    }
    ImGui::EndTable();
}

void InstallsScreen::draw_actions(
    const std::vector<std::pair<std::string, std::vector<std::string>>>& actions)
{
    float width = 0.0F;
    const float spacing = ImGui::GetStyle().ItemSpacing.x;
    for (const auto& action : actions)
    {
        width += ImGui::CalcTextSize(action.first.c_str()).x + ImGui::GetFontSize() * 2.0F +
                spacing;
    }

    const float available = ImGui::GetContentRegionAvail().x;
    if (width < available)
    {
        ImGui::SetCursorPosX(ImGui::GetCursorPosX() + available - width);
    }

    for (std::size_t index = 0; index < actions.size(); ++index)
    {
        if (index > 0)
        {
            ImGui::SameLine();
        }
        if (actions[index].first == "Open editor")
        {
            if (ImGui::Button(actions[index].first.c_str()))
            {
                start_action({EDITOR_PROGRAM, "editor"}, "se editor");
            }
        }
        else if (ImGui::Button(actions[index].first.c_str()))
        {
            start_action(actions[index].second, actions[index].first);
        }
    }
}

void InstallsScreen::start_action(std::vector<std::string> argv, std::string label)
{
    action_run_ = std::make_unique<CommandRun>(std::move(argv));
    action_run_->start();
    run_log_.adopt(*action_run_, std::move(label));
}

void InstallsScreen::draw_engine_card(const nlohmann::json* module)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::panel());
    ImGui::BeginChild("##sushihub_gui_installs_engine",
                       ImVec2(0.0F, ImGui::GetFontSize() * 8.0F), ImGuiChildFlags_Borders);

    if (module == nullptr)
    {
        draw_title("sushiengine", std::string());
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_faint());
        ImGui::TextUnformatted("reading...");
        ImGui::PopStyleColor();
        ImGui::EndChild();
        ImGui::PopStyleColor();
        return;
    }

    const std::string presence = field(*module, PRESENCE_KEY);
    draw_title("sushiengine", presence);

    const std::string& executable = workspace_.executable();

    if (presence == PRESENCE_ABSENT)
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
        ImGui::TextUnformatted("Neither a checkout nor a release is present yet.");
        ImGui::PopStyleColor();
        draw_actions({{"Install", {executable, "--json", "add", "sushiengine"}}});
    }
    else if (presence == PRESENCE_BINARY)
    {
        draw_fields({{"Version", field(*module, "version")},
                     {"Platform", field(*module, "platform")},
                     {"Licence expiry", field(*module, "licence_expiry")},
                     {"Newer release", field(*module, "latest_version")}});
        draw_actions({{"Open editor", {}},
                      {"Update", {executable, "--json", "update", "sushiengine"}},
                      {"Licence", {executable, "--json", "license"}}});
    }
    else
    {
        draw_fields({{"Branch", field(*module, "branch")},
                     {"Ahead/behind", field(*module, "ahead_behind")},
                     {"Build", "se build, in the terminal"},
                     {"Licence", "not needed"}});
        draw_actions({{"Open editor", {}},
                      {"Pull", {executable, "--json", "update", "sushiengine"}},
                      {"Details", {executable, "--json", "status"}}});
    }

    ImGui::EndChild();
    ImGui::PopStyleColor();
}

void InstallsScreen::draw_hub_card(const nlohmann::json* module)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::panel());
    ImGui::BeginChild("##sushihub_gui_installs_hub", ImVec2(0.0F, ImGui::GetFontSize() * 6.0F),
                       ImGuiChildFlags_Borders);

    if (module == nullptr)
    {
        draw_title("Sushi Hub", std::string());
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_faint());
        ImGui::TextUnformatted("reading...");
        ImGui::PopStyleColor();
        ImGui::EndChild();
        ImGui::PopStyleColor();
        return;
    }

    draw_title("Sushi Hub", field(*module, PRESENCE_KEY));
    draw_fields({{"Command", field(*module, "command")},
                 {"Alias", field(*module, "alias")},
                 {"Channel", field(*module, "channel")},
                 {"Current", field(*module, "current")}});

    ImGui::EndChild();
    ImGui::PopStyleColor();
}

}
}
