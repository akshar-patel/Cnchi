/*
 * cnchi_app.js
 *
 * Copyright 2016 Antergos
 *
 * This file is part of Cnchi.
 *
 * Cnchi is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License,
 * or any later version.
 *
 * Cnchi is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * The following additional terms are in effect as per Section 7 of the license:
 *
 * The preservation of all legal notices and author attributions in
 * the material or in the Appropriate Legal Notices displayed
 * by works containing it is required.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

'use strict';

/**
 * Whether or not the {@link CnchiApp} object has been created.
 */
let _cnchi_exists = false;


/**
 * The main application object. It follows the Singleton pattern.
 *
 * @prop {jQuery}   $header  A jQuery object corresponding to the app's header in the DOM.
 * @prop {boolean}  loaded   Whether or not the `page-loaded` event has fired.
 * @prop {String[]} cmds     The commands the app will accept from Python -> JS Bridge.
 * @prop {String[]} signals  The signals the app will allow to be sent via JS Bridge -> Python.
 * @prop {boolean}  dragging Whether or not the window is currently being dragged.
 */
class CnchiApp extends CnchiObject {

	constructor() {
		if ( false !== _cnchi_exists ) {
			return cnchi;
		}

		super();

		this.loaded = false;
		this.cmds = ['trigger_event'];
		this.signals = ['window-dragging-start', 'window-dragging-stop'];
		this.dragging = false;
		this.$header = $( '.header' );
		this._logger = null;
		this._bridge_message_queue = [];
		this.bmq_worker = null;
		this.$top_navigation_buttons = $( '.header_bottom .navigation_buttons .tabs' );

		this.register_event_handlers();
		this._start_bridge_message_queue_worker();
		this._maybe_unlock_top_level_tabs();
	}

	_maybe_unlock_top_level_tabs() {
		this.$top_navigation_buttons.children().each( ( index, element ) => {
			let $tab_button = $( element );

			$tab_button.removeClass( 'locked' );

			if ( $tab_button.hasClass( 'active' ) ) {
				// This button is for the current page. Don't unlock anymore buttons.
				return false;
			}
		} );
	}

	_start_bridge_message_queue_worker() {
		this.bmq_worker = setInterval( () => {
			if ( this._bridge_message_queue.length === 0 ) {
				return;
			}

			document.title = this._bridge_message_queue.shift();
		}, 100 );
	}

	/**
	 * Sends an allowed signal and optional arguments to the backend via the Python<->JS Bridge.
	 *
	 * @arg {...String|Array|Object} args The first arg should always be the name of the signal.
	 *
	 * @example
	 * emit_signal( 'do-some-action' );
	 * emit_signal( 'do-some-action', arg1, arg2 );
	 */
	emit_signal( ...args ) {
		let msg = '[', _args = [];

		if ( $.inArray( args[0], this.signals ) < 0 ) {
			this.logger.error( `cmd: "${args[0]}" is not in the list of allowed signals!` );
			return;
		}

		// Convert any non-string args to JSON strings so that we have a single string to send.
		for ( let _arg of args ) {
			if ( Array === typeof _arg || _arg instanceof Object ) {
				_arg = JSON.stringify( _arg );
			} else if ( 'string' === typeof _arg ) {
				_arg = `"${_arg}"`;
			}

			msg = `${msg}${_arg}, `;
		}

		msg = msg.replace( /, $/, '' );
		msg = `${msg}]`;

		this.logger.debug( `Emitting signal: "${msg}" via python bridge...` );

		this._bridge_message_queue.push( `_BR::${msg}` );
	}


	/**
	 * Header `mousedown` event callback. Intended to be used to implement window dragging.
	 * There is no official api for our use-case. Still, it appears to be possible. However,
	 * it doesn't work at the moment (probably because of some bug in GTK).
	 *
	 * @arg {jQuery.Event} event
	 *
	 * @todo Find a way to make this work.
	 */
	header_mousedown_cb( event ) {
		let $target = event.target ? $( event.target ) : event.currentTarget ? $( event.currentTarget ) : null;

		if ( null === $target ) {
			this.logger.debug( 'no target!' );
			return;
		}

		if ( $target.closest( '.no-drag' ).length || true === cnchi._dragging ) {
			this.logger.debug( `mousedown returning! ${cnchi._dragging}` );
			return;
		}

		cnchi._dragging = true;
		cnchi.emit_signal( 'window-dragging-start', 'window-dragging-start' );
	}

	/**
	 * Header `mouseup` event callback.
	 *
	 * @see CnchiApp.header_mousedown_cb
	 */
	header_mouseup_cb( event ) {
		let $target = event.target ? $( event.target ) : event.currentTarget ? $( event.currentTarget ) : null;

		if ( null === $target ) {
			this.logger.debug( 'no target!' );
			return;
		}

		if ( $target.closest( '.no-drag' ).length || false === cnchi._dragging ) {
			this.logger.debug( `mouseup returning! ${cnchi._dragging}` );
			return;
		}

		cnchi._dragging = false;

		cnchi.emit_signal( 'window-dragging-stop', 'window-dragging-stop' );
	}

	/**
	 * Handles messages sent from the backend via the Python<->JS Bridge. Messages are
	 * injected into the global scope as an `Object` referenced by a unique variable. The
	 * variable name is then passed to this method as a string so it can access the message.
	 *
	 * @arg msg_obj_var_name
	 */
	js_bridge_handler( msg_obj_var_name ) {
		let data, cmd, args;

		args = window[msg_obj_var_name].args;
		cmd = window[msg_obj_var_name].cmd;

		if ( ! cmd.length ) {
			this.logger.error( '"cmd" is required!', this.js_bridge_handler );
			return;
		}

		if ( $.inArray( cmd, this.cmds ) < 0 ) {
			this.logger.error(
				`cmd: "${cmd}" is not in the list of allowed commands!`, this.js_bridge_handler
			);
			return;
		}

		if ( args.length === 1 ) {
			args = args.pop();
		}

		this.logger.debug( `Running command: ${cmd} with args: ${args}...`,
						   this.js_bridge_handler );

		this[cmd]( args );
	}

	page_loaded_handler( event, page ) {
		if ( false === cnchi.loaded ) {
			cnchi.loaded = true;
		}
	}

	register_event_handlers() {
		//$(window).on('page-loaded', (event) => this.page_loaded_handler(event));
		//this.$header.on('mousedown', '*', this.header_mousedown_cb);
		//this.$header.on('mouseup', '*', this.header_mouseup_cb);
	}

	/**
	 * Triggers an event for signal received from backend with optional arguments.
	 *
	 * @arg {String|Array} event Either the event name or an Array where the first item is
	 *                           the event name and remaining items are args to pass to callback.
	 */
	trigger_event( event ) {
		let args = [];

		if ( Array.isArray( event ) ) {
			args = event;
			event = args.shift();

			if ( args.length === 1 ) {
				args = args.pop();
			}
		}

		this.logger.debug( `triggering event: ${event} with args: ${args}`, this.trigger_event );

		$( window ).trigger( event, args );
	}

}


if ( false === _cnchi_exists ) {
	window.cnchi = new CnchiApp();
	_cnchi_exists = true;
}

