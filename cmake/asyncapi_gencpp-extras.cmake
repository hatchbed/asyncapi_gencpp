cmake_minimum_required(VERSION 3.1)

macro(asyncapi_gencpp SPEC_FILE PREFIX OUTDIR)

    file(MAKE_DIRECTORY ${OUTDIR})
    add_custom_command(
        OUTPUT ${OUTDIR}/${PROJECT_NAME}/msg/messages.h
        COMMAND ${CMAKE_COMMAND} -E env ${asyncapi_gencpp_TOOL} ${SPEC_FILE} ${PREFIX} ${OUTDIR}
        DEPENDS ${SPEC_FILE}
    )

    add_custom_target(${PROJECT_NAME}_gencpp ALL
       DEPENDS ${OUTDIR}/${PROJECT_NAME}/msg/messages.h
    )

endmacro()