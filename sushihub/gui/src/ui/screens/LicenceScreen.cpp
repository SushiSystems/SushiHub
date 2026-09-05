/** @file LicenceScreen.cpp
 *  @brief Defines the two reports, the sign-in run and how the user code is shown.
 *  @author Mustafa Garip
 */

#include "ui/screens/LicenceScreen.hpp"

#include "ui/Browser.hpp"
#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"
#include "ui/widgets/ProgressBar.hpp"
#include "ui/widgets/TableView.hpp"

#include <imgui.h>

#include <cfloat>
#include <string>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command that reports who is signed in. */
constexpr const char* WHOAMI = "whoami";

/** @brief Holds the command that reports the licences an account holds. */
constexpr const char* LICENCE = "license";

/** @brief Holds the command that signs a person in through the device grant. */
constexpr const char* LOGIN = "login";

/** @brief Holds how many times the text size the user code is drawn at. */
constexpr float CODE_SCALE = 2.5F;

/** @brief Draws every message @p state holds, in the colour its level gives it. */
void draw_lines(const RunState& state)
{
    for (const LineEvent& line : state.lines)
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour(line.level));
        ImGui::TextWrapped("%s", line.message.c_str());
        ImGui::PopStyleColor();
    }
}

}

LicenceScreen::LicenceScreen(Workspace& workspace)
    : workspace_(workspace)
{
}

void LicenceScreen::draw()
{
    const bool refresh = ImGui::Button("Refresh");

    draw_report("Account", WHOAMI);
    draw_report("Licences", LICENCE);
    draw_sign_in();

    if (refresh)
    {
        workspace_.refresh(WHOAMI);
        workspace_.refresh(LICENCE);
    }
}

void LicenceScreen::draw_report(const char* title, const char* screen)
{
    CommandRun& run = workspace_.run_for(screen);
    run.poll();
    const RunState& state = run.state();

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText(title);
    ImGui::PopStyleColor();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (std::size_t index = 0; index < state.tables.size(); ++index)
    {
        const std::string id = std::string("##sushihub_gui_licence_") + screen + "_" +
                               std::to_string(index);
        Widgets::draw_table(id.c_str(), state.tables[index]);
    }

    draw_lines(state);
}

void LicenceScreen::draw_sign_in()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText("Sign in");
    ImGui::PopStyleColor();

    if (ImGui::Button(signing_in_ ? "Sign in again" : "Sign in"))
    {
        workspace_.refresh(LOGIN);
        signing_in_ = true;
    }

    if (!signing_in_)
    {
        return;
    }

    CommandRun& run = workspace_.run_for(LOGIN);
    run.poll();
    const RunState& state = run.state();

    draw_grant(read_device_grant(state));

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    if (state.pending_prompt.has_value())
    {
        std::string answer;
        if (prompt_.draw(*state.pending_prompt, answer))
        {
            run.answer_prompt(answer);
        }
    }

    Widgets::draw_event_log("##sushihub_gui_login_log", state, 0.0F);
}

void LicenceScreen::draw_grant(const DeviceGrant& grant)
{
    if (grant.user_code.empty())
    {
        return;
    }

    ImGui::TextUnformatted("Type this code on the sign-in page:");

    ImFont* font = ImGui::GetFont();
    const float size = ImGui::GetFontSize() * CODE_SCALE;
    const ImVec2 extent = font->CalcTextSizeA(size, FLT_MAX, 0.0F, grant.user_code.c_str());
    const ImVec2 origin = ImGui::GetCursorScreenPos();

    ImGui::GetWindowDrawList()->AddText(font, size, origin, ImGui::GetColorU32(ImGuiCol_Text),
                                        grant.user_code.c_str());
    ImGui::Dummy(extent);

    if (ImGui::Button("Copy code"))
    {
        ImGui::SetClipboardText(grant.user_code.c_str());
    }

    if (grant.verification_uri.empty())
    {
        return;
    }

    ImGui::SameLine();
    if (ImGui::Button("Open browser"))
    {
        open_in_browser(grant.verification_uri);
    }
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted(grant.verification_uri.c_str());
    ImGui::PopStyleColor();
}

}
}
