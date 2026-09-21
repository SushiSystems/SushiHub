/** @file InstallsScreen.cpp
 *  @brief Defines the two install cards, their presence chips, their fields and their actions.
 *  @author Mustafa Garip
 */

#include "ui/screens/InstallsScreen.hpp"

#include "model/InstallFacts.hpp"
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

/** @brief Holds the module whose card this screen draws first. */
constexpr const char* ENGINE = "sushiengine";

/** @brief Holds the presence a module reports when neither a checkout nor a release is there. */
constexpr const char* PRESENCE_ABSENT = "absent";

/** @brief Holds the presence a module reports when it is an unpacked release. */
constexpr const char* PRESENCE_BINARY = "binary";

/** @brief Holds the presence a module reports when it is a checkout elsewhere on disk. */
constexpr const char* PRESENCE_LINKED = "linked";

/** @brief Returns the colour @p presence's chip fills with, the same as on the modules screen. */
ImVec4 presence_colour(const std::string& presence)
{
    if (presence == PRESENCE_BINARY)
    {
        return Theme::accent();
    }
    if (presence == PRESENCE_LINKED)
    {
        return Theme::info();
    }
    if (presence == PRESENCE_ABSENT)
    {
        return Theme::ink_faint();
    }
    return Theme::ok();
}

/** @brief Returns the payload's `checked_updates`, false when it is missing. */
bool was_checked(const nlohmann::json& payload)
{
    return payload.value("checked_updates", false);
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
    CommandRun& offline = workspace_.run_for(STATUS_SCREEN);
    offline.poll();
    advance_update_check(offline);

    const nlohmann::json* payload = current_payload(offline);
    const bool checked = payload != nullptr && was_checked(*payload);

    const nlohmann::json* engine = nullptr;
    const nlohmann::json* hub = nullptr;
    if (payload != nullptr)
    {
        engine = InstallFacts::find_module(*payload, ENGINE);
        const auto found = payload->find("hub");
        hub = found != payload->end() && found->is_object() ? &*found : nullptr;
    }

    draw_engine_card(engine, checked);
    ImGui::Dummy(ImVec2(0.0F, ImGui::GetFontSize() * 0.5F));
    draw_hub_card(hub, checked);
}

void InstallsScreen::advance_update_check(const CommandRun& offline)
{
    if (update_check_ == nullptr && offline.state().finished)
    {
        update_check_ = std::make_unique<CommandRun>(std::vector<std::string>{
            workspace_.executable(), "--json", STATUS_SCREEN, "--check-updates"});
        update_check_->start();
        run_log_.adopt(*update_check_, "hub status --check-updates");
    }
    if (update_check_ != nullptr)
    {
        update_check_->poll();
    }
}

const nlohmann::json* InstallsScreen::current_payload(const CommandRun& offline) const
{
    if (update_check_ != nullptr && update_check_->state().result.has_value())
    {
        return &update_check_->state().result->payload;
    }
    if (offline.state().result.has_value())
    {
        return &offline.state().result->payload;
    }
    return nullptr;
}

bool InstallsScreen::checking() const
{
    return update_check_ != nullptr && !update_check_->state().result.has_value();
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
    const float baseline = ImGui::GetFontSize() * 0.3F;
    ImGui::GetWindowDrawList()->AddRectFilled(
        ImVec2(origin.x, origin.y + baseline), ImVec2(origin.x + side, origin.y + baseline + side),
        ImGui::ColorConvertFloat4ToU32(presence_colour(presence)));
    ImGui::Dummy(ImVec2(side, ImGui::GetFontSize()));
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
    ImGui::TextUnformatted(presence.c_str());
    ImGui::PopStyleColor();
}

void InstallsScreen::draw_reading()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_faint());
    ImGui::TextUnformatted("reading...");
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

void InstallsScreen::draw_actions(const std::vector<Action>& actions)
{
    const ImGuiStyle& style = ImGui::GetStyle();
    float width = 0.0F;
    for (const Action& action : actions)
    {
        width += ImGui::CalcTextSize(action.label).x + style.FramePadding.x * 2.0F +
                 style.ItemSpacing.x;
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
        if (ImGui::Button(actions[index].label))
        {
            start_action(actions[index].argv);
        }
    }
}

void InstallsScreen::start_action(const std::vector<std::string>& argv)
{
    std::string label;
    for (std::size_t index = 0; index < argv.size(); ++index)
    {
        if (argv[index] == "--json")
        {
            continue;
        }
        label += (label.empty() ? "" : " ") + (index == 0 && argv[0] == workspace_.executable()
                                                   ? std::string("hub")
                                                   : argv[index]);
    }
    action_run_ = std::make_unique<CommandRun>(argv);
    action_run_->start();
    run_log_.adopt(*action_run_, std::move(label));
}

void InstallsScreen::draw_engine_card(const nlohmann::json* module, bool checked)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::panel());
    ImGui::BeginChild("##sushihub_gui_installs_engine",
                      ImVec2(0.0F, ImGui::GetFontSize() * 9.0F), ImGuiChildFlags_Borders);

    if (module == nullptr)
    {
        draw_title(ENGINE, std::string());
        draw_reading();
        ImGui::EndChild();
        ImGui::PopStyleColor();
        return;
    }

    const std::string presence = InstallFacts::text(*module, "presence", PRESENCE_ABSENT);
    draw_title(ENGINE, presence);

    const std::string& hub = workspace_.executable();
    const Action open_editor{"Open editor", {"se", "editor"}};
    const std::string pending = checking() ? "checking..." : std::string();

    if (presence == PRESENCE_ABSENT)
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
        ImGui::TextUnformatted("Neither a checkout nor a release is present. hub add clones the "
                               "source with Git access, or installs the release with a licence.");
        ImGui::PopStyleColor();
        draw_actions({{"Install", {hub, "--json", "add", ENGINE}}});
    }
    else if (presence == PRESENCE_BINARY)
    {
        const std::string newer = pending.empty()
                                      ? InstallFacts::newer_release(*module, checked)
                                      : pending;
        draw_fields({{"Version", InstallFacts::text(*module, "version", "unknown")},
                     {"Platform", module->contains("binary") && (*module)["binary"].is_object()
                                      ? InstallFacts::text((*module)["binary"], "platform", "?")
                                      : std::string("?")},
                     {"Licence", InstallFacts::licence(*module)},
                     {"Newer release", newer}});
        draw_actions({open_editor,
                      {"Update", {hub, "--json", "update", ENGINE}},
                      {"Licence", {hub, "--json", "license"}}});
    }
    else
    {
        static const nlohmann::json no_source = nlohmann::json::object();
        const auto found = module->find("source");
        const nlohmann::json& source = found != module->end() && found->is_object() ? *found
                                                                                    : no_source;
        const std::string fetched = pending.empty()
                                        ? InstallFacts::last_fetch(source, InstallFacts::today_days())
                                        : pending;
        draw_fields({{"Branch", InstallFacts::text(source, "branch", "detached")},
                     {"Upstream", InstallFacts::distance(source)},
                     {"Fetched", fetched},
                     {"Build", "se build, in the terminal"}});
        draw_actions({open_editor,
                      {"Pull", {hub, "--json", "update", ENGINE}},
                      {"Details", {hub, "--json", STATUS_SCREEN}}});
    }

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_faint());
    ImGui::TextUnformatted("Open editor starts se editor, the one program besides hub this "
                           "window runs.");
    ImGui::PopStyleColor();

    ImGui::EndChild();
    ImGui::PopStyleColor();
}

void InstallsScreen::draw_hub_card(const nlohmann::json* hub, bool checked)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::panel());
    ImGui::BeginChild("##sushihub_gui_installs_hub", ImVec2(0.0F, ImGui::GetFontSize() * 6.0F),
                      ImGuiChildFlags_Borders);

    draw_title("Sushi Hub", std::string());
    if (hub == nullptr)
    {
        draw_reading();
    }
    else
    {
        draw_fields({{"Command", InstallFacts::text(*hub, "command", "hub")},
                     {"Alias", InstallFacts::alias(*hub)},
                     {"Channel", InstallFacts::text(*hub, "channel", "unknown")},
                     {"Current", checking() ? std::string("checking...")
                                            : InstallFacts::hub_currency(*hub, checked)}});
    }

    ImGui::EndChild();
    ImGui::PopStyleColor();
}

}
}
