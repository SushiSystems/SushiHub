/** @file FormOpener.hpp
 *  @brief Declares the seam a screen asks the shell to show one command's form through.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Accepts a screen's request to show the generated form of one command. */
class FormOpener
{
public:
    virtual ~FormOpener() = default;

    /**
     * @brief Shows @p command's form with @p arguments already entered.
     * @param command The catalogue name of the command; an unknown one is ignored.
     * @param arguments Values for the command's positional arguments, in declaration order.
     */
    virtual void open_form(const std::string& command,
                           const std::vector<std::string>& arguments) = 0;
};

}
}
