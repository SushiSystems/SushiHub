/** @file CommandsScreen.hpp
 *  @brief Declares the screen that keeps every catalogued `hub` command reachable.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Catalogue.hpp"
#include "model/RunLog.hpp"
#include "ui/CatalogueSource.hpp"
#include "ui/FormOpener.hpp"
#include "ui/Screen.hpp"
#include "ui/forms/GeneratedForm.hpp"

#include <array>
#include <cstddef>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Lists the catalogue's commands and opens each one's generated form beside the list. */
class CommandsScreen : public Screen, public FormOpener
{
public:
    /**
     * @brief Binds the screen to the catalogue it lists and the run every opened form reports to.
     * @param catalogue The `hub --describe` read the row list comes from.
     * @param covered_commands The commands a hand-drawn screen already covers, by catalogue name.
     * @param hub_executable The `hub` program a form's run is spawned from.
     * @param run_log The log the strip follows once an opened form's run starts.
     */
    CommandsScreen(CatalogueSource& catalogue,
                   const std::vector<std::string>& covered_commands,
                   std::string hub_executable,
                   RunLog& run_log);

    /** @brief Returns "Commands", the name the rail shows this destination under. */
    const char* name() const override;

    /** @brief Draws the search field, the row list and the opened form, if any. */
    void draw() override;

    /** @brief Opens @p command's form with @p arguments already entered. */
    void open_form(const std::string& command, const std::vector<std::string>& arguments) override;

private:
    /** @brief Holds how many characters the search field's text may have, the terminator included. */
    static constexpr std::size_t SEARCH_CAPACITY = 256;

    /** @brief Draws the search field at the top of the screen. */
    void draw_search();

    /** @brief Draws the row list in the left half of the region. */
    void draw_list();

    /** @brief Draws one row of the list for @p command. */
    void draw_row(const Command& command);

    /** @brief Draws the opened form, if any, in the right half of the region. */
    void draw_form_pane();

    /** @brief Reports whether @p command matches the current search text. */
    bool matches_search(const Command& command) const;

    /** @brief Returns the form of @p command, building it the first time it is asked for. */
    GeneratedForm* form_for(const std::string& command);

    /** @brief References the catalogue read the row list comes from. */
    CatalogueSource& catalogue_;

    /** @brief Holds the commands a hand-drawn screen already covers, by catalogue name. */
    std::vector<std::string> covered_commands_;

    /** @brief Holds the `hub` program a form's run is spawned from. */
    std::string hub_executable_;

    /** @brief References the log the strip follows once an opened form's run starts. */
    RunLog& run_log_;

    /** @brief Holds one form per command that has been opened, keyed by command name. */
    std::map<std::string, std::unique_ptr<GeneratedForm>> forms_;

    /** @brief Holds the command whose form is drawn on the right, empty when none is opened. */
    std::string active_command_;

    /** @brief Holds the search field's text, null-terminated. */
    std::array<char, SEARCH_CAPACITY> search_text_{};
};

}
}
