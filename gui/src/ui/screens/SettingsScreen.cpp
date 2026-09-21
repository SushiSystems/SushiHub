/** @file SettingsScreen.cpp
 *  @brief Defines the four setting rows, the sign-in flow and the doctor table's colouring.
 *  @author Mustafa Garip
 */

#include "ui/screens/SettingsScreen.hpp"

#include "ui/Browser.hpp"
#include "ui/Theme.hpp"
#include "ui/widgets/TableView.hpp"

#include <imgui.h>

#include <cfloat>
#include <cstddef>
#include <utility>
#include <vector>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command that reports who is signed in. */
constexpr const char* WHOAMI = "whoami";

/** @brief Holds the command that signs a person in through the device grant. */
constexpr const char* LOGIN = "login";

/** @brief Holds the command that forgets the stored session. */
constexpr const char* LOGOUT = "logout";

/** @brief Holds the command that reports the workspace and its modules. */
constexpr const char* STATUS = "status";

/** @brief Holds the command that inventories the machine. */
constexpr const char* DOCTOR = "doctor";

/** @brief Holds the command that provisions what the present modules declare. */
constexpr const char* INSTALL = "install";

/** @brief Holds the heading of the doctor column that carries a component's state. */
constexpr const char* STATUS_COLUMN = "Status";

/** @brief Holds the heading of the doctor column that carries a component's name. */
constexpr const char* COMPONENT_COLUMN = "Component";

/** @brief Holds the heading of the doctor column that carries the module a component serves. */
constexpr const char* OWNER_COLUMN = "Owner";

/** @brief Holds the heading of the doctor column that carries a component's note. */
constexpr const char* DETAIL_COLUMN = "Detail";

/** @brief Holds the state of a component that is there. */
constexpr const char* READY = "OK";

/** @brief Holds the state of a component that is asked for and is not there. */
constexpr const char* MISSING = "MISSING";

/** @brief Holds the state of a component no present module asks for. */
constexpr const char* NOT_NEEDED = "NOT NEEDED";

/** @brief Holds what a value column says while its run has produced nothing yet. */
constexpr const char* READING = "reading...";

/** @brief Holds how many times the text size the user code is drawn at. */
constexpr float CODE_SCALE = 2.5F;

/** @brief Holds the value column's width in font sizes. */
constexpr float VALUE_WIDTH = 15.0F;

/** @brief Holds the control column's width in font sizes. */
constexpr float CONTROL_WIDTH = 9.0F;

/** @brief Holds the doctor index column's width in font sizes. */
constexpr float INDEX_WIDTH = 2.5F;

/** @brief Holds the doctor state column's width in font sizes. */
constexpr float STATE_WIDTH = 8.0F;

/** @brief Counts how many components a doctor run found and how many it did not. */
struct DoctorTally
{
    /** @brief Holds how many components are there. */
    std::size_t ready = 0;

    /** @brief Holds how many components are asked for and are not there. */
    std::size_t missing = 0;
};

/** @brief Returns @p row's cell at @p index, empty when the row is shorter than that. */
std::string cell_at(const std::vector<std::string>& row, std::size_t index)
{
    return index < row.size() ? row[index] : std::string();
}

/** @brief Returns the string @p key holds in @p state's result payload, empty when it holds none. */
std::string payload_string(const RunState& state, const char* key)
{
    if (!state.result.has_value())
    {
        return {};
    }

    const nlohmann::json& payload = state.result->payload;
    const auto found = payload.find(key);
    if (found == payload.end() || !found->is_string())
    {
        return {};
    }
    return found->get<std::string>();
}

/** @brief Returns how many of @p state's doctor rows are ready and how many are missing. */
DoctorTally tally_of(const RunState& state)
{
    DoctorTally tally;
    for (const TableEvent& table : state.tables)
    {
        const std::size_t status_column = Widgets::column_index(table, STATUS_COLUMN);
        for (const std::vector<std::string>& row : table.rows)
        {
            const std::string status = cell_at(row, status_column);
            if (status == READY)
            {
                ++tally.ready;
            }
            else if (status == MISSING)
            {
                ++tally.missing;
            }
        }
    }
    return tally;
}

/** @brief Returns the colour the doctor state @p status is drawn in. */
ImVec4 state_colour(const std::string& status)
{
    if (status == READY)
    {
        return Theme::ok();
    }
    if (status == MISSING)
    {
        return Theme::critical();
    }
    return Theme::ink_faint();
}

/** @brief Draws @p text in @p colour on one line. */
void draw_tinted(const ImVec4& colour, const char* text)
{
    ImGui::PushStyleColor(ImGuiCol_Text, colour);
    ImGui::TextUnformatted(text);
    ImGui::PopStyleColor();
}

}

SettingsScreen::SettingsScreen(Workspace& workspace, RunLog& log)
    : workspace_(workspace),
      log_(log)
{
}

const char* SettingsScreen::name() const
{
    return "Settings";
}

void SettingsScreen::draw()
{
    const float size = ImGui::GetFontSize();

    if (ImGui::BeginTable("##sushihub_gui_settings_rows", 3,
                          ImGuiTableFlags_BordersInnerH | ImGuiTableFlags_PadOuterX))
    {
        ImGui::TableSetupColumn("##setting", ImGuiTableColumnFlags_WidthStretch);
        ImGui::TableSetupColumn("##value", ImGuiTableColumnFlags_WidthFixed, VALUE_WIDTH * size);
        ImGui::TableSetupColumn("##control", ImGuiTableColumnFlags_WidthFixed,
                                CONTROL_WIDTH * size);

        draw_account_row();
        draw_workspace_row();
        draw_alias_row();
        draw_dependencies_row();

        ImGui::EndTable();
    }

    draw_sign_in();
    draw_doctor_table();
}

void SettingsScreen::draw_row(const char* title, const char* sentence, const std::string& value,
                              const Control& control)
{
    ImGui::TableNextRow();

    ImGui::TableSetColumnIndex(0);
    ImGui::TextUnformatted(title);
    draw_tinted(Theme::ink_dim(), sentence);

    ImGui::TableSetColumnIndex(1);
    if (value.empty())
    {
        draw_tinted(Theme::ink_faint(), READING);
    }
    else
    {
        ImGui::TextUnformatted(value.c_str());
    }

    ImGui::TableSetColumnIndex(2);
    control();
}

void SettingsScreen::draw_account_row()
{
    CommandRun& run = workspace_.run_for(WHOAMI);
    run.poll();

    const std::string email = payload_string(run.state(), "email");
    const bool signed_in = !email.empty();
    const std::string value = signed_in ? email
                              : (run.state().finished ? std::string("Not signed in")
                                                      : std::string());

    draw_row("Sushi Account", "The account this machine holds its licences under.", value,
             [this, signed_in]()
             {
                 if (signed_in)
                 {
                     if (ImGui::Button("Sign out"))
                     {
                         start(LOGOUT, "hub logout");
                         workspace_.refresh(WHOAMI);
                         signing_in_ = false;
                     }
                     return;
                 }

                 if (ImGui::Button(signing_in_ ? "Sign in again" : "Sign in"))
                 {
                     start(LOGIN, "hub login");
                     signing_in_ = true;
                 }
             });
}

void SettingsScreen::draw_workspace_row()
{
    CommandRun& run = workspace_.run_for(STATUS);
    run.poll();

    draw_row("Workspace", "The folder `hub` runs the stack from; it is chosen when `hub` starts.",
             payload_string(run.state(), "workspace"),
             []()
             {
                 ImGui::BeginDisabled();
                 ImGui::Button("Change");
                 ImGui::EndDisabled();
             });
}

void SettingsScreen::draw_alias_row()
{
    draw_row("The `sh` alias", "The short name for `hub`; the installer writes it, not this window.",
             workspace_.executable(),
             [this]()
             {
                 ImGui::Checkbox("##sushihub_gui_settings_alias", &alias_enabled_);
             });
}

void SettingsScreen::draw_dependencies_row()
{
    CommandRun& run = workspace_.run_for(DOCTOR);
    run.poll();

    const RunState& state = run.state();
    const DoctorTally tally = tally_of(state);
    const std::string value = state.tables.empty()
                                  ? std::string()
                                  : std::to_string(tally.ready) + " ready, " +
                                        std::to_string(tally.missing) + " missing";

    draw_row("Dependencies", "What the present modules declare and what the machine has of it.",
             value,
             [this]()
             {
                 if (ImGui::Button("Provision"))
                 {
                     start(INSTALL, "hub install");
                 }
             });
}

void SettingsScreen::draw_sign_in()
{
    if (!signing_in_)
    {
        return;
    }

    CommandRun& run = workspace_.run_for(LOGIN);
    run.poll();
    const RunState& state = run.state();

    draw_grant(read_device_grant(state));

    if (state.pending_prompt.has_value())
    {
        std::string answer;
        if (prompt_.draw(*state.pending_prompt, answer))
        {
            run.answer_prompt(answer);
        }
    }
}

void SettingsScreen::draw_grant(const DeviceGrant& grant)
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
    draw_tinted(Theme::ink_dim(), grant.verification_uri.c_str());
}

void SettingsScreen::draw_doctor_table()
{
    CommandRun& run = workspace_.run_for(DOCTOR);
    const RunState& state = run.state();
    const float size = ImGui::GetFontSize();

    ImGui::Dummy(ImVec2(0.0F, size * 0.5F));
    draw_tinted(Theme::ink_dim(), "What `hub doctor` found, in the order it reports it.");

    std::size_t index = 0;
    for (std::size_t table_index = 0; table_index < state.tables.size(); ++table_index)
    {
        const TableEvent& table = state.tables[table_index];
        const std::size_t component_column = Widgets::column_index(table, COMPONENT_COLUMN);
        const std::size_t owner_column = Widgets::column_index(table, OWNER_COLUMN);
        const std::size_t detail_column = Widgets::column_index(table, DETAIL_COLUMN);
        const std::size_t status_column = Widgets::column_index(table, STATUS_COLUMN);

        const std::string id = "##sushihub_gui_doctor_" + std::to_string(table_index);
        if (!ImGui::BeginTable(id.c_str(), 4,
                               ImGuiTableFlags_RowBg | ImGuiTableFlags_BordersInnerH |
                                   ImGuiTableFlags_PadOuterX))
        {
            continue;
        }

        ImGui::TableSetupColumn("#", ImGuiTableColumnFlags_WidthFixed, INDEX_WIDTH * size);
        ImGui::TableSetupColumn("Dependency", ImGuiTableColumnFlags_WidthStretch);
        ImGui::TableSetupColumn("Note", ImGuiTableColumnFlags_WidthStretch);
        ImGui::TableSetupColumn("State", ImGuiTableColumnFlags_WidthFixed, STATE_WIDTH * size);
        ImGui::TableHeadersRow();

        for (const std::vector<std::string>& row : table.rows)
        {
            const std::string status = cell_at(row, status_column);
            const bool needed = status != NOT_NEEDED;

            ImGui::TableNextRow();

            ImGui::TableSetColumnIndex(0);
            draw_tinted(Theme::ink_faint(), std::to_string(++index).c_str());

            ImGui::TableSetColumnIndex(1);
            draw_tinted(needed ? Theme::ink() : Theme::ink_faint(),
                        cell_at(row, component_column).c_str());
            draw_tinted(Theme::ink_faint(), cell_at(row, owner_column).c_str());

            ImGui::TableSetColumnIndex(2);
            draw_tinted(needed ? Theme::ink_dim() : Theme::ink_faint(),
                        cell_at(row, detail_column).c_str());

            ImGui::TableSetColumnIndex(3);
            draw_tinted(state_colour(status), status.c_str());
        }

        ImGui::EndTable();
    }
}

void SettingsScreen::start(const char* command, std::string label)
{
    workspace_.refresh(command);
    log_.adopt(workspace_.run_for(command), std::move(label));
}

}
}
