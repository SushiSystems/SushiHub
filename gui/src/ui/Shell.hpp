/** @file Shell.hpp
 *  @brief Declares the window's frame: the title bar, the rail, the screen region and the strip.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunLog.hpp"
#include "model/Workspace.hpp"
#include "ui/CatalogueSource.hpp"
#include "ui/FormOpener.hpp"
#include "ui/Screen.hpp"
#include "ui/chrome/NavRail.hpp"
#include "ui/chrome/TitleBar.hpp"
#include "ui/screens/CommandsScreen.hpp"
#include "ui/widgets/ActivityStrip.hpp"

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Returns the commands a hand-drawn screen already covers, so no form repeats them. */
const std::vector<std::string>& covered_commands();

/** @brief Draws the frame and gives the region between the rail and the strip to one screen. */
class Shell : public FormOpener
{
public:
    /** @brief Builds the shell over the `hub` program found on the search path. */
    Shell();

    /** @brief Builds the shell over @p hub_executable, which every run is spawned from. */
    explicit Shell(std::string hub_executable);

    /** @brief Draws one frame of the title bar, the rail, the active screen and the strip. */
    void draw();

    /** @brief Returns the name of the screen the rail currently selects. */
    const char* active_screen() const;

    void open_form(const std::string& command, const std::vector<std::string>& arguments) override;

private:
    /** @brief Draws the rail beside the region the active screen owns. */
    void draw_body();

    /** @brief Holds the workspace every run is spawned from. */
    Workspace workspace_;

    /** @brief Holds the catalogue read the commands screen lists. */
    CatalogueSource catalogue_;

    /** @brief Holds the run the strip reports, whichever screen started it. */
    RunLog run_log_;

    /** @brief Draws the top row and nothing else. */
    TitleBar title_bar_;

    /** @brief Draws the destinations and records which one is chosen. */
    NavRail rail_;

    /** @brief Draws the run the strip follows and owns whether it is expanded. */
    Widgets::ActivityStrip strip_;

    /** @brief Holds the four destinations in the order the rail lists them. */
    std::vector<std::unique_ptr<Screen>> screens_;

    /** @brief Holds each destination's name, as the rail reads them each frame. */
    std::vector<const char*> screen_names_;

    /** @brief Points at the commands screen a form request is forwarded to. */
    CommandsScreen* commands_;

    /** @brief Holds the index into screens_ of the screen being drawn. */
    std::size_t active_index_;
};

}
}
