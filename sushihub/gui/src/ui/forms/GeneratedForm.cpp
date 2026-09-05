/** @file GeneratedForm.cpp
 *  @brief Defines the widget per parameter type, the argument vector they build and the run.
 *  @author Mustafa Garip
 */

#include "ui/forms/GeneratedForm.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"
#include "ui/widgets/ProgressBar.hpp"

#include <imgui.h>

#include <algorithm>
#include <cstring>
#include <sstream>
#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Writes @p value into @p text, truncated to what the buffer holds. */
template <std::size_t Capacity>
void assign(std::array<char, Capacity>& text, const std::string& value)
{
    text.fill('\0');
    const std::size_t length = std::min(value.size(), text.size() - 1);
    std::memcpy(text.data(), value.data(), length);
}

/** @brief Returns @p value as the text a widget shows, empty for a null default. */
std::string default_text(const nlohmann::json& value)
{
    if (value.is_null())
    {
        return std::string();
    }
    if (value.is_string())
    {
        return value.get<std::string>();
    }
    return value.dump();
}

/** @brief Returns the words of @p text, which is how a repeated parameter is typed. */
std::vector<std::string> words(const std::string& text)
{
    std::istringstream stream(text);
    std::vector<std::string> collected;
    std::string word;
    while (stream >> word)
    {
        collected.push_back(word);
    }
    return collected;
}

/** @brief Returns the spelling an option is given on the command line. */
const std::string& option_flag(const Parameter& parameter)
{
    static const std::string none;
    return parameter.flags.empty() ? none : parameter.flags.front();
}

/** @brief Returns the flags an input of @p type accepts characters under. */
ImGuiInputTextFlags input_flags(ParameterType type)
{
    if (type == ParameterType::integer)
    {
        return ImGuiInputTextFlags_CharsDecimal;
    }
    if (type == ParameterType::number)
    {
        return ImGuiInputTextFlags_CharsScientific;
    }
    return 0;
}

}

GeneratedForm::GeneratedForm(Command command, std::string ss_executable)
    : command_(std::move(command)),
      ss_executable_(std::move(ss_executable)),
      fields_(command_.parameters.size())
{
    adopt_defaults();
}

void GeneratedForm::prefill_arguments(const std::vector<std::string>& values)
{
    std::size_t taken = 0;
    for (std::size_t index = 0; index < command_.parameters.size() && taken < values.size();
         ++index)
    {
        if (command_.parameters[index].is_argument)
        {
            assign(fields_[index].text, values[taken++]);
        }
    }
}

void GeneratedForm::draw()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText(command_.name.c_str());
    ImGui::PopStyleColor();

    if (!command_.help.empty())
    {
        ImGui::TextWrapped("%s", command_.help.c_str());
    }

    for (std::size_t index = 0; index < command_.parameters.size(); ++index)
    {
        ImGui::PushID(static_cast<int>(index));
        draw_field(command_.parameters[index], fields_[index]);
        ImGui::PopID();
    }

    draw_controls();
    draw_run();
}

const Command& GeneratedForm::command() const
{
    return command_;
}

void GeneratedForm::adopt_defaults()
{
    for (std::size_t index = 0; index < command_.parameters.size(); ++index)
    {
        const Parameter& parameter = command_.parameters[index];
        if (parameter.type == ParameterType::boolean)
        {
            fields_[index].flag = parameter.default_value.is_boolean() &&
                                  parameter.default_value.get<bool>();
            continue;
        }
        assign(fields_[index].text, default_text(parameter.default_value));
    }
}

void GeneratedForm::draw_field(const Parameter& parameter, Field& field)
{
    const std::string label = parameter.name + (parameter.required ? " *" : "");

    if (parameter.type == ParameterType::boolean)
    {
        ImGui::Checkbox(label.c_str(), &field.flag);
    }
    else if (parameter.type == ParameterType::choice)
    {
        draw_choice(parameter, field);
    }
    else
    {
        ImGui::SetNextItemWidth(-220.0F);
        ImGui::InputText(label.c_str(), field.text.data(), field.text.size(),
                         input_flags(parameter.type));
        if (parameter.type == ParameterType::path)
        {
            ImGui::SameLine();
            if (ImGui::Button("Browse"))
            {
                ImGui::SetKeyboardFocusHere(-1);
            }
        }
    }

    if (!parameter.help.empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
        ImGui::TextWrapped("%s", parameter.help.c_str());
        ImGui::PopStyleColor();
    }
}

void GeneratedForm::draw_choice(const Parameter& parameter, Field& field)
{
    const std::string label = parameter.name + (parameter.required ? " *" : "");
    ImGui::SetNextItemWidth(-220.0F);

    if (!ImGui::BeginCombo(label.c_str(), field.text.data()))
    {
        return;
    }
    for (const std::string& choice : parameter.choices)
    {
        const bool selected = choice == field.text.data();
        if (ImGui::Selectable(choice.c_str(), selected))
        {
            assign(field.text, choice);
        }
    }
    ImGui::EndCombo();
}

void GeneratedForm::draw_controls()
{
    const bool busy = run_ != nullptr && !run_->state().finished;
    const bool runnable = ready() && !busy;

    ImGui::BeginDisabled(!runnable);
    if (ImGui::Button(run_ == nullptr ? "Run" : "Run again"))
    {
        run_ = std::unique_ptr<CommandRun>(new CommandRun(build_argv()));
        run_->start();
    }
    ImGui::EndDisabled();

    if (!ready())
    {
        ImGui::SameLine();
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour("warn"));
        ImGui::TextUnformatted("A required parameter is empty.");
        ImGui::PopStyleColor();
    }
}

void GeneratedForm::draw_run()
{
    if (run_ == nullptr)
    {
        return;
    }

    run_->poll();
    const RunState& state = run_->state();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    if (state.pending_prompt.has_value())
    {
        std::string answer;
        if (prompt_.draw(*state.pending_prompt, answer))
        {
            run_->answer_prompt(answer);
        }
    }

    Widgets::draw_event_log("##sushihub_gui_form_log", state, 0.0F);
}

std::vector<std::string> GeneratedForm::build_argv() const
{
    std::vector<std::string> argv{ss_executable_, "--json", command_.name};
    std::vector<std::string> positionals;

    for (std::size_t index = 0; index < command_.parameters.size(); ++index)
    {
        const Parameter& parameter = command_.parameters[index];
        const Field& field = fields_[index];

        if (parameter.type == ParameterType::boolean)
        {
            if (field.flag && !option_flag(parameter).empty())
            {
                argv.push_back(option_flag(parameter));
            }
            continue;
        }

        const std::string text(field.text.data());
        if (text.empty())
        {
            continue;
        }

        const std::vector<std::string> values = parameter.multiple ? words(text)
                                                                   : std::vector<std::string>{text};
        for (const std::string& value : values)
        {
            if (parameter.is_argument)
            {
                positionals.push_back(value);
            }
            else if (!option_flag(parameter).empty())
            {
                argv.push_back(option_flag(parameter));
                argv.push_back(value);
            }
        }
    }

    argv.insert(argv.end(), positionals.begin(), positionals.end());
    return argv;
}

bool GeneratedForm::ready() const
{
    for (std::size_t index = 0; index < command_.parameters.size(); ++index)
    {
        const Parameter& parameter = command_.parameters[index];
        if (!parameter.required || parameter.type == ParameterType::boolean)
        {
            continue;
        }
        if (fields_[index].text[0] == '\0')
        {
            return false;
        }
    }
    return true;
}

}
}
