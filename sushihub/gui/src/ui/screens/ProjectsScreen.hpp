/** @file ProjectsScreen.hpp
 *  @brief Declares the screen that lists the registered projects and the buttons that change them.
 *  @author Mustafa Garip
 */

#pragma once

#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"
#include "model/Workspace.hpp"
#include "ui/widgets/TableView.hpp"

#include <array>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the projects run, the form that adds one, and the buttons each row carries. */
class ProjectsScreen
{
public:
    /** @brief Binds the screen to the workspace the projects run is asked from. */
    explicit ProjectsScreen(Workspace& workspace);

    /** @brief Lets an editor that is still running outlive the screen instead of waiting on it. */
    ~ProjectsScreen();

    ProjectsScreen(const ProjectsScreen&) = delete;
    ProjectsScreen& operator=(const ProjectsScreen&) = delete;

    /** @brief Draws one frame of the screen. */
    void draw();

private:
    /** @brief Holds the engine an Open button spawns, the one program this screen names. */
    static constexpr const char* ENGINE_EXECUTABLE = "se";

    /** @brief Holds how many characters one field of the add form takes, terminator included. */
    static constexpr std::size_t TEXT_CAPACITY = 512;

    /** @brief Holds one spawned editor and the output nothing reads as events. */
    struct Editor
    {
        /** @brief Holds the lines the editor writes, dropped as they arrive. */
        std::unique_ptr<LineQueue> output;

        /** @brief Holds the editor while it runs. */
        std::unique_ptr<Process> process;
    };

    /** @brief Draws the path field, the name field and the Add button they fill. */
    void draw_add_form();

    /** @brief Draws the line that stands in for the table when the registry holds nothing. */
    void draw_empty_state(const RunState& state);

    /** @brief Draws the Open and Remove buttons that end @p row. */
    void draw_row_actions(const TableEvent& table, const std::vector<std::string>& row);

    /** @brief Draws what the started add or remove has produced. */
    void draw_action();

    /** @brief Starts @p argv as the one add or remove the screen keeps at a time. */
    void start_action(std::vector<std::string> argv);

    /** @brief Reports whether a finished action still has to be read back into the list. */
    bool adopt_action();

    /** @brief Spawns the engine's editor on the project directory @p path. */
    void open_editor(const std::string& path);

    /** @brief Drops what every editor has written and forgets the ones that have exited. */
    void collect_editors();

    /** @brief References the workspace the projects run is asked from. */
    Workspace& workspace_;

    /** @brief Holds the directory the add form registers, null-terminated. */
    std::array<char, TEXT_CAPACITY> path_{};

    /** @brief Holds the name the add form lists that directory under, empty for its own name. */
    std::array<char, TEXT_CAPACITY> name_{};

    /** @brief Holds the add or remove a button started, null until one is pressed. */
    std::unique_ptr<CommandRun> action_;

    /** @brief Records that the finished action has been read back into the list. */
    bool action_adopted_ = false;

    /** @brief Holds every editor this screen has spawned and not yet seen exit. */
    std::vector<Editor> editors_;

    /** @brief Holds why the last Open spawned nothing, empty when it spawned an editor. */
    std::string editor_error_;
};

}
}
