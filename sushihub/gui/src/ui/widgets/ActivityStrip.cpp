/** @file ActivityStrip.cpp
 *  @brief Defines the strip's summary line, its progress fill and the log it expands into.
 *  @author Mustafa Garip
 */

#include "ui/widgets/ActivityStrip.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"

#include <imgui.h>

#include <algorithm>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Holds how many lines of events the expanded region shows. */
constexpr float LOG_LINES = 8.0F;

/** @brief Holds the text the strip carries while no run has been adopted. */
constexpr const char* IDLE_LABEL = "no run yet";

/** @brief Returns the completed fraction of @p state, one once its result has arrived. */
float completed_fraction(const RunState& state)
{
    if (state.result.has_value())
    {
        return 1.0F;
    }
    if (!state.progress.has_value())
    {
        return 0.0F;
    }

    const ProgressEvent& progress = *state.progress;
    double fraction = 0.0;
    if (progress.fraction.has_value())
    {
        fraction = *progress.fraction;
    }
    else if (progress.count > 0)
    {
        fraction = static_cast<double>(progress.index) / static_cast<double>(progress.count);
    }
    return static_cast<float>(std::min(std::max(fraction, 0.0), 1.0));
}

/** @brief Returns the colour the bar is filled in for @p state. */
ImVec4 fill_colour(const RunState& state)
{
    if (!state.result.has_value())
    {
        return Theme::accent();
    }
    return state.result->ok ? Theme::ok() : Theme::critical();
}

/** @brief Returns the word the right of the strip reports @p state's outcome with. */
const char* outcome_text(const RunState& state)
{
    if (state.result.has_value())
    {
        return state.result->ok ? "rc=0" : "rc!=0";
    }
    return state.finished ? "ended" : "running";
}

/** @brief Returns the colour @p state's outcome word is drawn in. */
ImVec4 outcome_colour(const RunState& state)
{
    if (!state.result.has_value())
    {
        return Theme::ink_faint();
    }
    return state.result->ok ? Theme::ok() : Theme::critical();
}

/** @brief Draws @p text in @p colour on one line without wrapping. */
void draw_text(const char* text, const ImVec4& colour)
{
    ImGui::PushStyleColor(ImGuiCol_Text, colour);
    ImGui::TextUnformatted(text);
    ImGui::PopStyleColor();
}

}

float ActivityStrip::height() const
{
    const float line = ImGui::GetFontSize() * 2.2F;
    if (!expanded_)
    {
        return line;
    }
    return line + ImGui::GetFontSize() * (LOG_LINES + 0.6F);
}

void ActivityStrip::draw(RunLog& log)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::panel());
    ImGui::BeginChild("##sushihub_activity_strip", ImVec2(0.0F, height()), ImGuiChildFlags_None,
                      ImGuiWindowFlags_NoScrollbar);

    draw_summary(log);

    if (expanded_ && log.has_run())
    {
        Widgets::draw_event_log("##sushihub_activity_log", log.run().state(),
                                ImGui::GetFontSize() * LOG_LINES);
    }

    ImGui::EndChild();
    ImGui::PopStyleColor();
}

void ActivityStrip::draw_summary(RunLog& log)
{
    const ImVec2 origin = ImGui::GetCursorScreenPos();
    const float row_height = ImGui::GetFontSize() * 2.0F;

    if (ImGui::InvisibleButton("##sushihub_activity_toggle",
                               ImVec2(ImGui::GetContentRegionAvail().x, row_height)))
    {
        expanded_ = !expanded_;
    }

    ImGui::SetCursorScreenPos(ImVec2(origin.x + ImGui::GetFontSize() * 0.6F,
                                     origin.y + ImGui::GetFontSize() * 0.5F));
    draw_text(expanded_ ? "v" : ">", Theme::ink_faint());

    ImGui::SameLine();
    draw_text(log.has_run() ? log.label().c_str() : IDLE_LABEL,
              log.has_run() ? Theme::ink() : Theme::ink_faint());

    if (!log.has_run())
    {
        return;
    }

    const RunState& state = log.run().state();

    ImGui::SameLine(0.0F, ImGui::GetFontSize());
    ImGui::PushStyleColor(ImGuiCol_PlotHistogram, fill_colour(state));
    ImGui::PushStyleColor(ImGuiCol_FrameBg, Theme::ground());
    ImGui::ProgressBar(completed_fraction(state),
                       ImVec2(ImGui::GetFontSize() * 10.0F, ImGui::GetFontSize() * 0.6F), "");
    ImGui::PopStyleColor(2);

    const char* outcome = outcome_text(state);
    const float right =
        ImGui::GetContentRegionMax().x - ImGui::CalcTextSize(outcome).x - ImGui::GetFontSize();
    ImGui::SameLine(right);
    draw_text(outcome, outcome_colour(state));
}

}
}
}
