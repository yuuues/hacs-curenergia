const t=globalThis,e=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),i=new WeakMap;let r=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const s=this.t;if(e&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=i.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&i.set(s,t))}return t}toString(){return this.cssText}};const o=e?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return(t=>new r("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:n,defineProperty:a,getOwnPropertyDescriptor:l,getOwnPropertyNames:c,getOwnPropertySymbols:d,getPrototypeOf:h}=Object,p=globalThis,u=p.trustedTypes,_=u?u.emptyScript:"",$=p.reactiveElementPolyfillSupport,m=(t,e)=>t,g={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},y=(t,e)=>!n(t,e),f={attribute:!0,type:String,converter:g,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),p.litPropertyMetadata??=new WeakMap;let v=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=f){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&a(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:r}=l(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const o=i?.call(this);r?.call(this,e),this.requestUpdate(t,o,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??f}static _$Ei(){if(this.hasOwnProperty(m("elementProperties")))return;const t=h(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(m("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(m("properties"))){const t=this.properties,e=[...c(t),...d(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(o(t))}else void 0!==t&&e.push(o(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const s=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((s,i)=>{if(e)s.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const e of i){const i=document.createElement("style"),r=t.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=e.cssText,s.appendChild(i)}})(s,this.constructor.elementStyles),s}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const r=(void 0!==s.converter?.toAttribute?s.converter:g).toAttribute(e,s.type);this._$Em=t,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:g;this._$Em=i;const o=r.fromAttribute(e,t.type);this[i]=o??this._$Ej?.get(i)??o,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(void 0!==t){const o=this.constructor;if(!1===i&&(r=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??y)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),!0!==r||void 0!==o)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};v.elementStyles=[],v.shadowRootOptions={mode:"open"},v[m("elementProperties")]=new Map,v[m("finalized")]=new Map,$?.({ReactiveElement:v}),(p.reactiveElementVersions??=[]).push("2.1.2");const b=globalThis,w=t=>t,A=b.trustedTypes,x=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,S="?"+k,C=`<${S}>`,P=document,N=()=>P.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,T=Array.isArray,M="[ \t\n\f\r]",O=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,R=/-->/g,H=/>/g,D=RegExp(`>|${M}(?:([^\\s"'>=/]+)(${M}*=${M}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),I=/'/g,W=/"/g,L=/^(?:script|style|textarea|title)$/i,z=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),j=Symbol.for("lit-noChange"),B=Symbol.for("lit-nothing"),F=new WeakMap,V=P.createTreeWalker(P,129);function q(t,e){if(!T(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==x?x.createHTML(e):e}const G=(t,e)=>{const s=t.length-1,i=[];let r,o=2===e?"<svg>":3===e?"<math>":"",n=O;for(let e=0;e<s;e++){const s=t[e];let a,l,c=-1,d=0;for(;d<s.length&&(n.lastIndex=d,l=n.exec(s),null!==l);)d=n.lastIndex,n===O?"!--"===l[1]?n=R:void 0!==l[1]?n=H:void 0!==l[2]?(L.test(l[2])&&(r=RegExp("</"+l[2],"g")),n=D):void 0!==l[3]&&(n=D):n===D?">"===l[0]?(n=r??O,c=-1):void 0===l[1]?c=-2:(c=n.lastIndex-l[2].length,a=l[1],n=void 0===l[3]?D:'"'===l[3]?W:I):n===W||n===I?n=D:n===R||n===H?n=O:(n=D,r=void 0);const h=n===D&&t[e+1].startsWith("/>")?" ":"";o+=n===O?s+C:c>=0?(i.push(a),s.slice(0,c)+E+s.slice(c)+k+h):s+k+(-2===c?e:h)}return[q(t,o+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class J{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,o=0;const n=t.length-1,a=this.parts,[l,c]=G(t,e);if(this.el=J.createElement(l,s),V.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=V.nextNode())&&a.length<n;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(E)){const e=c[o++],s=i.getAttribute(t).split(k),n=/([.?@])?(.*)/.exec(e);a.push({type:1,index:r,name:n[2],strings:s,ctor:"."===n[1]?Y:"?"===n[1]?tt:"@"===n[1]?et:X}),i.removeAttribute(t)}else t.startsWith(k)&&(a.push({type:6,index:r}),i.removeAttribute(t));if(L.test(i.tagName)){const t=i.textContent.split(k),e=t.length-1;if(e>0){i.textContent=A?A.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],N()),V.nextNode(),a.push({type:2,index:++r});i.append(t[e],N())}}}else if(8===i.nodeType)if(i.data===S)a.push({type:2,index:r});else{let t=-1;for(;-1!==(t=i.data.indexOf(k,t+1));)a.push({type:7,index:r}),t+=k.length-1}r++}}static createElement(t,e){const s=P.createElement("template");return s.innerHTML=t,s}}function K(t,e,s=t,i){if(e===j)return e;let r=void 0!==i?s._$Co?.[i]:s._$Cl;const o=U(e)?void 0:e._$litDirective$;return r?.constructor!==o&&(r?._$AO?.(!1),void 0===o?r=void 0:(r=new o(t),r._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=r:s._$Cl=r),void 0!==r&&(e=K(t,r._$AS(t,e.values),r,i)),e}class Z{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??P).importNode(e,!0);V.currentNode=i;let r=V.nextNode(),o=0,n=0,a=s[0];for(;void 0!==a;){if(o===a.index){let e;2===a.type?e=new Q(r,r.nextSibling,this,t):1===a.type?e=new a.ctor(r,a.name,a.strings,this,t):6===a.type&&(e=new st(r,this,t)),this._$AV.push(e),a=s[++n]}o!==a?.index&&(r=V.nextNode(),o++)}return V.currentNode=P,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class Q{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=B,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=K(this,t,e),U(t)?t===B||null==t||""===t?(this._$AH!==B&&this._$AR(),this._$AH=B):t!==this._$AH&&t!==j&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>T(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==B&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(P.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=J.createElement(q(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new Z(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=F.get(t.strings);return void 0===e&&F.set(t.strings,e=new J(t)),e}k(t){T(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const r of t)i===e.length?e.push(s=new Q(this.O(N()),this.O(N()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=w(t).nextSibling;w(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class X{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=B,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=B}_$AI(t,e=this,s,i){const r=this.strings;let o=!1;if(void 0===r)t=K(this,t,e,0),o=!U(t)||t!==this._$AH&&t!==j,o&&(this._$AH=t);else{const i=t;let n,a;for(t=r[0],n=0;n<r.length-1;n++)a=K(this,i[s+n],e,n),a===j&&(a=this._$AH[n]),o||=!U(a)||a!==this._$AH[n],a===B?t=B:t!==B&&(t+=(a??"")+r[n+1]),this._$AH[n]=a}o&&!i&&this.j(t)}j(t){t===B?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class Y extends X{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===B?void 0:t}}class tt extends X{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==B)}}class et extends X{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=K(this,t,e,0)??B)===j)return;const s=this._$AH,i=t===B&&s!==B||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==B&&(s===B||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class st{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){K(this,t)}}const it=b.litHtmlPolyfillSupport;it?.(J,Q),(b.litHtmlVersions??=[]).push("3.3.3");const rt=globalThis;class ot extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let r=i._$litPart$;if(void 0===r){const t=s?.renderBefore??null;i._$litPart$=r=new Q(e.insertBefore(N(),t),t,void 0,s??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return j}}ot._$litElement$=!0,ot.finalized=!0,rt.litElementHydrateSupport?.({LitElement:ot});const nt=rt.litElementPolyfillSupport;nt?.({LitElement:ot}),(rt.litElementVersions??=[]).push("4.2.2");const at="—";function lt(t,e,s,i){const r={minimumFractionDigits:s,maximumFractionDigits:i};let o;try{o=new Intl.NumberFormat(t,r)}catch(t){if(!(t instanceof RangeError))throw t;o=new Intl.NumberFormat("en",r)}return o.format(e).replace(/[  ]/g," ")}function ct(t){const e=/^(\d{4})-(\d{2})-(\d{2})/.exec(t);return e?`${e[3]}/${e[2]}/${e[1]}`:t}function dt(t,e){return null===e?at:`${lt(t,e,0,2)} kWh`}function ht(t,e){return null===e?at:`${lt(t,e,2,2)} €`}function pt(t,e){return null===e?at:`${lt(t,e,4,4)} €/kWh`}function ut(t,e){return null===e?at:`${lt(t,e,1,1)} %`}function _t(t,e,s){if(null===e)return at;const i="kwh"===s?"kWh":"€",r="kwh"===s?[0,2]:[2,2],o=lt(t,Math.abs(e),...r);return`${0===Number(Math.abs(e).toFixed(r[1]))?"":e<0?"−":"+"}${o} ${i}`}function $t(t,e){return null===e?at:`${lt(t,e,0,2)} %`}const mt={es:{status_ok:"Cuadra",status_mismatch:"No cuadra",status_estimated:"Lectura estimada",status_no_data:"Sin datos suficientes",status_unreadable:"No se pudo leer",status_gas:"Gas (sin casar)",pill_estimated:"estimada",pill_unreadable:"no se pudo leer",tab_electricity:"Luz",tab_gas:"Gas",col_period:"Periodo",col_kwh_invoice:"kWh factura",col_kwh_edata:"kWh Datadis",col_delta_kwh:"Δ kWh",col_amount:"Importe",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Potencia + energía: factura {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_number:"Nº de factura",detail_issued:"Emitida el {date}",detail_window:"Ventana e-data: {period}",detail_group:"Comparada junto con: {numbers}",detail_in_group_of:"Regularizada en la factura {number}",detail_periods:"kWh por periodo (P1 / P2 / P3)",detail_concepts:"Conceptos",detail_vat:"IVA {rate} sobre {base}: {amount}",detail_energy_price:"Precio de la energía: {price}",detail_problems:"Avisos de lectura",detail_period_row:"{period}: factura {invoice} / Datadis {edata}",row_covers:"abarca {n} facturas",detail_own_kwh:"Esta factura: {kwh}",detail_group_heading:"Comparación del grupo ({n} facturas)",card_title:"Facturas",loading:"Cargando…",empty:"Todavía no hay facturas",error:"No se pudieron cargar las facturas",retry:"Reintentar",chart_title:"Importe por factura",chart_empty:"Sin datos para el gráfico",panel_title:"Facturas",panel_billed_12m:"Facturado en 12 meses",panel_kwh_delta:"Diferencia de kWh",panel_estimated_count:"Facturas con lectura estimada",panel_unreadable:"Correos que no se pudieron leer",panel_unsupported:"Correos no soportados",panel_last_check:"Último correo comprobado",panel_never:"Nunca",panel_mail_error:"No se pudo acceder al buzón",panel_all_entries:"Todas las cuentas",panel_entry:"Cuenta",editor_title:"Título",editor_supply:"Pestaña inicial",editor_max_invoices:"Número máximo de facturas",editor_entry_id:"Cuenta de correo (opcional)",editor_entry_all:"Todas"},en:{status_ok:"Matches",status_mismatch:"Does not match",status_estimated:"Estimated reading",status_no_data:"Not enough data",status_unreadable:"Could not be read",status_gas:"Gas (not matched)",pill_estimated:"estimated",pill_unreadable:"could not be read",tab_electricity:"Electricity",tab_gas:"Gas",col_period:"Period",col_kwh_invoice:"Invoice kWh",col_kwh_edata:"Datadis kWh",col_delta_kwh:"Δ kWh",col_amount:"Amount",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Power + energy: invoice {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_number:"Invoice no.",detail_issued:"Issued on {date}",detail_window:"e-data window: {period}",detail_group:"Compared together with: {numbers}",detail_in_group_of:"Settled by invoice {number}",detail_periods:"kWh by period (P1 / P2 / P3)",detail_concepts:"Line items",detail_vat:"VAT {rate} on {base}: {amount}",detail_energy_price:"Energy price: {price}",detail_problems:"Reading warnings",detail_period_row:"{period}: invoice {invoice} / Datadis {edata}",row_covers:"covers {n} invoices",detail_own_kwh:"This invoice: {kwh}",detail_group_heading:"Group comparison ({n} invoices)",card_title:"Invoices",loading:"Loading…",empty:"No invoices yet",error:"Could not load the invoices",retry:"Retry",chart_title:"Amount per invoice",chart_empty:"No data for the chart",panel_title:"Invoices",panel_billed_12m:"Billed in 12 months",panel_kwh_delta:"kWh difference",panel_estimated_count:"Invoices with estimated reading",panel_unreadable:"E-mails that could not be read",panel_unsupported:"Unsupported e-mails",panel_last_check:"Last e-mail checked",panel_never:"Never",panel_mail_error:"Could not access the mailbox",panel_all_entries:"All accounts",panel_entry:"Account",editor_title:"Title",editor_supply:"Initial tab",editor_max_invoices:"Maximum number of invoices",editor_entry_id:"Mail account (optional)",editor_entry_all:"All"}};function gt(t){return t.locale?.language||t.language||"en"}function yt(t,e,s){const i=(gt(t).toLowerCase().startsWith("es")?mt.es:mt.en)[e];return s?i.replace(/\{(\w+)\}/g,(t,e)=>e in s?String(s[e]):t):i}const ft=[{supply:"electricity",label:"tab_electricity"},{supply:"gas",label:"tab_gas"}],vt=[{key:"p1",name:"P1"},{key:"p2",name:"P2"},{key:"p3",name:"P3"}];function bt(t,e){return e.period_end.localeCompare(t.period_end)||e.issue_date.localeCompare(t.issue_date)||e.number.localeCompare(t.number)}class wt extends ot{constructor(){super(),this.contracts=[],this.supply="electricity",this._expanded=new Set}render(){const t=(this.contracts??[]).filter(t=>t.supply===this.supply);return z`
      <div class="tabs" role="tablist">
        ${ft.map(({supply:t,label:e})=>z`
            <button
              class="tab"
              role="tab"
              type="button"
              aria-selected=${t===this.supply?"true":"false"}
              @click=${()=>this._selectSupply(t)}
            >
              ${yt(this.hass,e)}
            </button>
          `)}
      </div>
      ${0===t.length?z`<div class="empty">${yt(this.hass,"empty")}</div>`:t.map(e=>this._renderContract(e,t.length>1))}
    `}_renderContract(t,e){const s=[...t.invoices].sort(bt),i=this.maxInvoices,r=i&&i>0?s.slice(0,i):s,o="gas"===this.supply?["col_period","col_kwh","col_m3","col_amount","col_price_kwh"]:["col_period","col_kwh_invoice","col_kwh_edata","col_delta_kwh","col_amount","col_delta_eur"];return z`
      ${e?z`<h3 class="contract-name">${t.name}</h3>`:B}
      <div class="scroll">
        <table>
          <thead>
            <tr>
              ${o.map(t=>z`<th>${yt(this.hass,t)}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${r.map(e=>this._renderRow(t,e,o.length))}
          </tbody>
        </table>
      </div>
    `}_renderRow(t,e,s){const i=gt(this.hass),r=`${t.entry_id}|${t.contract}|${e.number}`,o=this._expanded.has(r),n=e.comparison?.group.length??0,a=`color: var(${function(t){switch(t){case"ok":return"--success-color";case"no_cuadra":return"--warning-color";case"no_leida":return"--error-color";default:return"--secondary-text-color"}}(e.status)})`,l=()=>this._toggle(r),c=z`
      <td>
        ${function(t,e){const s=ct(t),i=ct(e);return t.slice(0,4)===e.slice(0,4)?`${s.slice(0,5)} – ${i}`:`${s} – ${i}`}(e.period_start,e.period_end)}
        ${e.estimated?z`<span class="pill">${yt(this.hass,"pill_estimated")}</span>`:B}
        ${"no_leida"===e.status?z`<span class="pill error">${yt(this.hass,"pill_unreadable")}</span>`:B}
        ${n>1?z`<span class="note">${yt(this.hass,"row_covers",{n:n})}</span>`:B}
      </td>
    `,d=e.comparison,h="gas"===e.supply?z`
            <td>${dt(i,e.kwh)}</td>
            <td>${function(t,e){return null===e?at:`${lt(t,e,0,2)} m³`}(i,e.m3)}</td>
            <td>${ht(i,e.total)}</td>
            <td>${pt(i,e.price_kwh)}</td>
          `:z`
            <td>${dt(i,d?.invoice_kwh??e.kwh)}</td>
            <td>${dt(i,d?.edata_kwh??null)}</td>
            <td style=${a}>${_t(i,d?.delta_kwh??null,"kwh")}</td>
            <td>${ht(i,e.total)}</td>
            <td style=${a}>${_t(i,d?.delta_eur??null,"eur")}</td>
          `;return z`
      <tr
        class="row ${e.estimated?"estimated":""}"
        tabindex="0"
        aria-expanded=${o?"true":"false"}
        @click=${l}
        @keydown=${t=>{"Enter"!==t.key&&" "!==t.key||(t.preventDefault(),l())}}
      >
        ${c} ${h}
      </tr>
      ${o?z`<tr class="detail">
            <td colspan=${s}>${this._renderDetail(e)}</td>
          </tr>`:B}
    `}_renderDetail(t){const e=gt(this.hass),s="gas"!==t.supply,i=t.comparison;return z`
      <div class="detail-body">
        <ul>
          ${t.concepts.map(t=>z`<li><span>${t.label}</span><span>${ht(e,t.amount)}</span></li>`)}
        </ul>
        <div>
          ${yt(this.hass,"detail_vat",{rate:$t(e,t.vat.rate),base:ht(e,t.vat.base),amount:ht(e,t.vat.amount)})}
        </div>
        ${s?this._renderElectricityDetail(t,i):B}
        ${t.in_group_of?z`<div>
              ${yt(this.hass,"detail_in_group_of",{number:t.in_group_of})}
            </div>`:B}
        ${i&&i.group.length>1?z`<div>
              ${yt(this.hass,"detail_group",{numbers:i.group.join(", ")})}
            </div>`:B}
      </div>
    `}_renderElectricityDetail(t,e){const s=gt(this.hass),i=e?.invoice_periods??t.periods,r=e?.edata_periods??null,o=null!==i||null!==r,n=(e?.group.length??0)>1;return z`
      ${n?z`<div>${yt(this.hass,"detail_own_kwh",{kwh:dt(s,t.kwh)})}</div>
            <strong>
              ${yt(this.hass,"detail_group_heading",{n:e?.group.length??0})}
            </strong>`:B}
      ${o?z`<ul>
            ${vt.map(({key:t,name:e})=>z`<li>
                  ${yt(this.hass,"detail_period_row",{period:e,invoice:dt(s,i?.[t]??null),edata:dt(s,r?.[t]??null)})}
                </li>`)}
          </ul>`:B}
      ${e?z`<div>
            ${yt(this.hass,"detail_power_energy",{invoice:ht(s,e.invoice_eur),edata:ht(s,e.edata_eur)})}
            (${yt(this.hass,"detail_delta_pct",{pct:ut(s,e.delta_pct)})})
          </div>`:B}
      <div>
        ${yt(this.hass,"detail_energy_price",{price:pt(s,t.energy_price_kwh)})}
      </div>
    `}_toggle(t){const e=new Set(this._expanded);e.delete(t)||e.add(t),this._expanded=e}_selectSupply(t){t!==this.supply&&(this.supply=t,this._expanded=new Set,this.dispatchEvent(new CustomEvent("supply-changed",{detail:{supply:t},bubbles:!0,composed:!0})))}}wt.properties={hass:{attribute:!1},contracts:{attribute:!1},supply:{type:String},maxInvoices:{type:Number,attribute:"max-invoices"},_expanded:{state:!0}},wt.styles=((t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new r(i,t,s)})`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .tabs {
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--divider-color);
      margin-bottom: 8px;
    }
    .tab {
      appearance: none;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }
    .tab[aria-selected="true"] {
      border-bottom-color: var(--primary-color);
      color: var(--primary-text-color);
      font-weight: 500;
    }
    .contract-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      padding: 8px 6px;
      text-align: right;
      white-space: nowrap;
    }
    th:first-child,
    td:first-child {
      text-align: left;
    }
    th {
      border-bottom: 1px solid var(--divider-color);
      color: var(--secondary-text-color);
      font-weight: 500;
    }
    tr.row {
      cursor: pointer;
    }
    tr.row:hover,
    tr.row:focus-visible {
      background: var(--secondary-background-color, transparent);
    }
    tr.row:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: -2px;
    }
    tr.row td {
      border-bottom: 1px solid var(--divider-color);
    }
    tr.row.estimated {
      color: var(--secondary-text-color);
    }
    .pill {
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      color: var(--secondary-text-color);
      font-size: 0.8em;
      margin-left: 6px;
      padding: 1px 6px;
    }
    .pill.error {
      border-color: var(--error-color);
      color: var(--error-color);
    }
    .note {
      color: var(--secondary-text-color);
      display: block;
      font-size: 0.85em;
    }
    tr.detail td {
      background: var(--secondary-background-color, transparent);
      border-bottom: 1px solid var(--divider-color);
      text-align: left;
      white-space: normal;
    }
    .detail-body {
      display: grid;
      gap: 6px;
      padding: 4px 0;
    }
    .detail-body ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .detail-body li {
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .empty {
      color: var(--secondary-text-color);
      padding: 16px 0;
      text-align: center;
    }
    @media (max-width: 450px) {
      th,
      td {
        padding: 6px 4px;
      }
    }
  `,customElements.get("curenergia-invoice-table")||customElements.define("curenergia-invoice-table",wt);
