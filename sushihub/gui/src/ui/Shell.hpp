/** @file Shell.hpp
 *  @brief Declares the window's frame: a sidebar of screens and commands, and the pane beside it.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/Workspace.hpp"
#include "ui/CatalogueSource.hpp"
#include "ui/FormOpener.hpp"
#include "ui/forms/GeneratedForm.hpp"
#include "ui/screens/DependenciesScreen.hpp"
#include "ui/screens/LicenceScreen.hpp"
#include "ui/screens/ModulesScreen.hpp"
#include "ui/screens/ProjectsScreen.hpp"
#include "ui/screens/StatusScreen.hpp"

#include <cstddef>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the application frame and routes to the screen or form the sidebar selects. */
class Shell : public FormOpener
{
public:
    /** @brief Builds the shell over the `ss` program found on the search path. */
    Shell();

    /** @brief Builds the shell over @p ss_executable, which every run is spawned from. */
    explicit Shell(std::string ss_executable);

    /** @brief Draws one frame of the sidebar and of whatever the sidebar has selected. */
    void draw();

    /** @brief Returns the name of the screen or command the sidebar currently selects. */
    const std::string& active_screen() const;

    void open_form(const std::string& command, const std::vector<std::string>& arguments) override;

private:
    /** @brief Draws the sidebar and records what the user selects in it. */
    void draw_sidebar();

    /** @brief Draws the generated commands under the five screens, once they are known. */
    void draw_command_list();

    /** @brief Draws the pane the selected screen or form owns. */
    void draw_pane();

    /** @brief Returns the form of @p command, building it the first time it is asked for. */
    GeneratedForm* form_for(const std::string& command);

    /** @brief Holds the workspace every run is spawned from. */
    Workspace workspace_;

    /** @brief Holds the catalogue read the sidebar's command list comes from. */
    CatalogueSource catalogue_;

    /** @brief Draws what the workspace reports about itself. */
    StatusScreen status_screen_;

    /** @brief Draws the modules and the command each one can be given. */
    ModulesScreen modules_screen_;

    /** @brief Draws what the machine has and what it is missing. */
    DependenciesScreen dependencies_screen_;

    /** @brief Draws the account, its licences and the sign-in. */
    LicenceScreen licence_screen_;

    /** @brief Draws the registered projects and the buttons that change the registry. */
    ProjectsScreen projects_screen_;

    /** @brief Holds one form per command that has been opened, keyed by command name. */
    std::map<std::string, std::unique_ptr<GeneratedForm>> forms_;

    /** @brief Holds the screen names in the order the sidebar lists them. */
    std::vector<std::string> screen_names_;

    /** @brief Holds the index into screen_names_ of the screen being drawn. */
    std::size_t active_index_;

    /** @brief Holds the selected command's name, empty while a screen is selected. */
    std::string active_command_;
};

}
}
