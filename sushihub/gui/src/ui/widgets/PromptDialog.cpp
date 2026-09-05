/** @file PromptDialog.cpp
 *  @brief Defines the modal's lifetime, its default answer and how it is submitted.
 *  @author Mustafa Garip
 */

#include "ui/widgets/PromptDialog.hpp"

#include <imgui.h>

#include <algorithm>
#include <cstring>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Holds the identifier and the title the modal is drawn under. */
constexpr const char* POPUP_TITLE = "The command is asking##sushihub_gui_prompt";

/** @brief Holds the flags that keep the modal at the size its content needs. */
constexpr ImGuiWindowFlags POPUP_FLAGS = ImGuiWindowFlags_AlwaysAutoResize;

}

bool PromptDialog::draw(const PromptEvent& prompt, std::string& answer)
{
    adopt(prompt);

    if (!ImGui::IsPopupOpen(POPUP_TITLE))
    {
        ImGui::OpenPopup(POPUP_TITLE);
    }

    const ImVec2 centre = ImGui::GetMainViewport()->GetCenter();
    ImGui::SetNextWindowPos(centre, ImGuiCond_Appearing, ImVec2(0.5F, 0.5F));

    bool answered = false;
    if (ImGui::BeginPopupModal(POPUP_TITLE, nullptr, POPUP_FLAGS))
    {
        ImGui::TextWrapped("%s", prompt.message.c_str());
        ImGui::SetNextItemWidth(360.0F);
        const bool entered = ImGui::InputText("##sushihub_gui_prompt_answer", answer_.data(),
                                              answer_.size(),
                                              ImGuiInputTextFlags_EnterReturnsTrue);
        const bool pressed = ImGui::Button("Answer");
        answered = entered || pressed;

        if (answered)
        {
            answer.assign(answer_.data());
            ImGui::CloseCurrentPopup();
        }
        ImGui::EndPopup();
    }

    return answered;
}

void PromptDialog::adopt(const PromptEvent& prompt)
{
    if (prompt_id_ == prompt.id)
    {
        return;
    }

    prompt_id_ = prompt.id;
    answer_.fill('\0');

    if (prompt.default_answer.has_value())
    {
        const std::string& value = *prompt.default_answer;
        const std::size_t length = std::min(value.size(), answer_.size() - 1);
        std::memcpy(answer_.data(), value.data(), length);
    }
}

}
}
}
