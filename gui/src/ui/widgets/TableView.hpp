/** @file TableView.hpp
 *  @brief Declares the drawing of one table event and the per-row decisions a screen adds to it.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

#include <cstddef>
#include <functional>
#include <string>
#include <string_view>
#include <vector>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/** @brief Names how strongly one row is drawn. */
enum class RowEmphasis
{
    normal,
    dimmed
};

/** @brief Returns the emphasis the row of cells it is given is drawn with. */
using RowEmphasisRule = std::function<RowEmphasis(const std::vector<std::string>&)>;

/** @brief Draws whatever ends the row of cells it is given, in the trailing column. */
using RowActionRule = std::function<void(const std::vector<std::string>&)>;

/** @brief Carries the per-row decisions a screen makes about the table it draws. */
struct TableDecoration
{
    /** @brief Returns a row's emphasis; unset draws every row normally. */
    RowEmphasisRule emphasis;

    /** @brief Holds the trailing column's heading; empty leaves that column out. */
    std::string action_column;

    /** @brief Draws a row's trailing cell; unset leaves that column out. */
    RowActionRule action;
};

/**
 * @brief Draws @p table with its title, its column headings and one row per record.
 * @param id The identifier ImGui keeps the table's column widths under.
 * @param decoration The emphasis and the trailing column the caller adds, none by default.
 */
void draw_table(const char* id, const TableEvent& table, const TableDecoration& decoration = {});

/**
 * @brief Finds the column @p heading names.
 * @param table The table whose columns are searched, ignoring letter case.
 * @return The column's index, or the column count when no column carries that heading.
 */
std::size_t column_index(const TableEvent& table, std::string_view heading);

}
}
}
