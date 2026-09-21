/** @file TableView.cpp
 *  @brief Defines the ImGui table one table event is drawn as.
 *  @author Mustafa Garip
 */

#include "ui/widgets/TableView.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

#include <cctype>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Holds the flags every table drawn here shares. */
constexpr ImGuiTableFlags TABLE_FLAGS = ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg |
                                        ImGuiTableFlags_SizingStretchProp |
                                        ImGuiTableFlags_Resizable;

/** @brief Reports whether @p left and @p right are the same text ignoring letter case. */
bool same_text(std::string_view left, std::string_view right)
{
    if (left.size() != right.size())
    {
        return false;
    }
    for (std::size_t index = 0; index < left.size(); ++index)
    {
        const unsigned char first = static_cast<unsigned char>(left[index]);
        const unsigned char second = static_cast<unsigned char>(right[index]);
        if (std::tolower(first) != std::tolower(second))
        {
            return false;
        }
    }
    return true;
}

/** @brief Draws the cells of @p row that the table declares columns for. */
void draw_cells(const TableEvent& table, const std::vector<std::string>& row)
{
    for (std::size_t cell = 0; cell < table.columns.size(); ++cell)
    {
        ImGui::TableSetColumnIndex(static_cast<int>(cell));
        ImGui::TextUnformatted(cell < row.size() ? row[cell].c_str() : "");
    }
}

}

void draw_table(const char* id, const TableEvent& table, const TableDecoration& decoration)
{
    if (table.columns.empty())
    {
        return;
    }

    const bool has_action = !decoration.action_column.empty() && static_cast<bool>(decoration.action);
    const int columns = static_cast<int>(table.columns.size()) + (has_action ? 1 : 0);

    if (!table.title.empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
        ImGui::SeparatorText(table.title.c_str());
        ImGui::PopStyleColor();
    }

    if (!ImGui::BeginTable(id, columns, TABLE_FLAGS))
    {
        return;
    }

    for (const std::string& column : table.columns)
    {
        ImGui::TableSetupColumn(column.c_str());
    }
    if (has_action)
    {
        ImGui::TableSetupColumn(decoration.action_column.c_str());
    }
    ImGui::TableHeadersRow();

    int row_id = 0;
    for (const std::vector<std::string>& row : table.rows)
    {
        ImGui::TableNextRow();
        ImGui::PushID(row_id++);

        const bool dimmed = static_cast<bool>(decoration.emphasis) &&
                            decoration.emphasis(row) == RowEmphasis::dimmed;
        if (dimmed)
        {
            ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
        }
        draw_cells(table, row);
        if (dimmed)
        {
            ImGui::PopStyleColor();
        }

        if (has_action)
        {
            ImGui::TableSetColumnIndex(static_cast<int>(table.columns.size()));
            decoration.action(row);
        }
        ImGui::PopID();
    }

    ImGui::EndTable();
}

std::size_t column_index(const TableEvent& table, std::string_view heading)
{
    for (std::size_t index = 0; index < table.columns.size(); ++index)
    {
        if (same_text(table.columns[index], heading))
        {
            return index;
        }
    }
    return table.columns.size();
}

}
}
}
