/** @file CommandsScreen.cpp
 *  @brief Defines the search, the row list, the covered-command note and the opened form.
 *  @author Mustafa Garip
 */

#include "ui/screens/CommandsScreen.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

#include <algorithm>
#include <cctype>
#include <cstring>
#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Returns @p text with every letter folded to lower case. */
std::string to_lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(),
                   [](unsigned char letter) { return static_cast<char>(std::tolower(letter)); });
    return text;
}

/** @brief Returns whether @p haystack contains @p needle, case-insensitively. */
bool contains(const std::string& haystack, const std::string& needle)
{
    return to_lower(haystack).find(to_lower(needle)) != std::string::npos;
}

}

CommandsScreen::CommandsScreen(CatalogueSource& catalogue,
                               const std::vector<std::string>& covered_commands,
                               std::string hub_executable,
                               RunLog& run_log)
    : catalogue_(catalogue),
      covered_commands_(covered_commands),
      hub_executable_(std::move(hub_executable)),
      run_log_(run_log)
{
}

const char* CommandsScreen::name() const
{
    return "Commands";
}

void CommandsScreen::draw()
{
    catalogue_.poll();

    if (!catalogue_.finished())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
        ImGui::TextUnformatted("reading...");
        ImGui::PopStyleColor();
        return;
    }

    if (!catalogue_.error().empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::critical());
        ImGui::TextWrapped("%s", catalogue_.error().c_str());
        ImGui::PopStyleColor();
        return;
    }

    draw_search();

    const float list_width = ImGui::GetFontSize() * 22.0F;
    ImGui::BeginChild("##sushihub_gui_commands_list", ImVec2(list_width, 0.0F));
    draw_list();
    ImGui::EndChild();

    ImGui::SameLine();

    ImGui::BeginChild("##sushihub_gui_commands_form", ImVec2(0.0F, 0.0F));
    draw_form_pane();
    ImGui::EndChild();
}

void CommandsScreen::open_form(const std::string& command, const std::vector<std::string>& arguments)
{
    GeneratedForm* form = form_for(command);
    if (form == nullptr)
    {
        return;
    }

    form->prefill_arguments(arguments);
    active_command_ = command;
}

void CommandsScreen::draw_search()
{
    ImGui::SetNextItemWidth(ImGui::GetFontSize() * 22.0F);
    ImGui::InputTextWithHint("##sushihub_gui_commands_search", "Search commands",
                             search_text_.data(), search_text_.size());
}

void CommandsScreen::draw_list()
{
    for (const Command& command : catalogue_.catalogue().commands)
    {
        if (!matches_search(command))
        {
            continue;
        }
        draw_row(command);
    }
}

void CommandsScreen::draw_row(const Command& command)
{
    ImGui::PushID(command.name.c_str());

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink());
    ImGui::TextUnformatted(command.name.c_str());
    ImGui::PopStyleColor();

    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
    ImGui::TextWrapped("%s", command.help.c_str());
    ImGui::PopStyleColor();

    const bool covered =
        std::find(covered_commands_.begin(), covered_commands_.end(), command.name) !=
        covered_commands_.end();
    if (covered)
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_faint());
        ImGui::TextUnformatted("Already reachable from its own screen.");
        ImGui::PopStyleColor();
    }

    if (ImGui::SmallButton("Open"))
    {
        active_command_ = command.name;
    }

    ImGui::Separator();
    ImGui::PopID();
}

void CommandsScreen::draw_form_pane()
{
    if (active_command_.empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::ink_dim());
        ImGui::TextUnformatted("Open a command to fill in its form.");
        ImGui::PopStyleColor();
        return;
    }

    GeneratedForm* form = form_for(active_command_);
    if (form != nullptr)
    {
        form->draw();
    }
}

bool CommandsScreen::matches_search(const Command& command) const
{
    if (search_text_[0] == '\0')
    {
        return true;
    }
    const std::string needle(search_text_.data());
    return contains(command.name, needle) || contains(command.help, needle);
}

GeneratedForm* CommandsScreen::form_for(const std::string& command)
{
    const auto found = forms_.find(command);
    if (found != forms_.end())
    {
        return found->second.get();
    }

    for (const Command& entry : catalogue_.catalogue().commands)
    {
        if (entry.name != command)
        {
            continue;
        }
        auto form = std::unique_ptr<GeneratedForm>(new GeneratedForm(entry, hub_executable_, run_log_));
        const auto inserted = forms_.emplace(command, std::move(form));
        return inserted.first->second.get();
    }

    return nullptr;
}

}
}
