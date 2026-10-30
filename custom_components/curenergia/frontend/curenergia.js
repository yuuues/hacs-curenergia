const t=globalThis,e=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let s=class{constructor(t,e,r){if(this._$cssResult$=!0,r!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const i=this.t;if(e&&void 0===t){const e=void 0!==i&&1===i.length;e&&(t=r.get(i)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&r.set(i,t))}return t}toString(){return this.cssText}};const a=(t,...e)=>{const r=1===t.length?t[0]:e.reduce((e,i,r)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[r+1],t[0]);return new s(r,t,i)},n=e?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new s("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:o,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:c,getOwnPropertySymbols:h,getPrototypeOf:p}=Object,u=globalThis,_=u.trustedTypes,m=_?_.emptyScript:"",g=u.reactiveElementPolyfillSupport,v=(t,e)=>t,$={toAttribute(t,e){switch(e){case Boolean:t=t?m:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},y=(t,e)=>!o(t,e),f={attribute:!0,type:String,converter:$,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=f){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),r=this.getPropertyDescriptor(t,i,e);void 0!==r&&l(this.prototype,t,r)}}static getPropertyDescriptor(t,e,i){const{get:r,set:s}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:r,set(e){const a=r?.call(this);s?.call(this,e),this.requestUpdate(t,a,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??f}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const t=this.properties,e=[...c(t),...h(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(n(t))}else void 0!==t&&e.push(n(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const i=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((i,r)=>{if(e)i.adoptedStyleSheets=r.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const e of r){const r=document.createElement("style"),s=t.litNonce;void 0!==s&&r.setAttribute("nonce",s),r.textContent=e.cssText,i.appendChild(r)}})(i,this.constructor.elementStyles),i}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),r=this.constructor._$Eu(t,i);if(void 0!==r&&!0===i.reflect){const s=(void 0!==i.converter?.toAttribute?i.converter:$).toAttribute(e,i.type);this._$Em=t,null==s?this.removeAttribute(r):this.setAttribute(r,s),this._$Em=null}}_$AK(t,e){const i=this.constructor,r=i._$Eh.get(t);if(void 0!==r&&this._$Em!==r){const t=i.getPropertyOptions(r),s="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:$;this._$Em=r;const a=s.fromAttribute(e,t.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(t,e,i,r=!1,s){if(void 0!==t){const a=this.constructor;if(!1===r&&(s=this[t]),i??=a.getPropertyOptions(t),!((i.hasChanged??y)(s,e)||i.useDefault&&i.reflect&&s===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:r,wrapped:s},a){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),!0!==s||void 0!==a)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===r&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,r=this[e];!0!==t||this._$AL.has(e)||void 0===r||this.C(e,void 0,i,r)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[v("elementProperties")]=new Map,b[v("finalized")]=new Map,g?.({ReactiveElement:b}),(u.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,w=t=>t,k=x.trustedTypes,A=k?k.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,S="?"+C,P=`<${S}>`,M=document,U=()=>M.createComment(""),I=t=>null===t||"object"!=typeof t&&"function"!=typeof t,N=Array.isArray,H="[ \t\n\f\r]",O=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,T=/-->/g,R=/>/g,D=RegExp(`>|${H}(?:([^\\s"'>=/]+)(${H}*=${H}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),z=/'/g,W=/"/g,L=/^(?:script|style|textarea|title)$/i,j=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),q=j(1),B=j(2),F=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),K=new WeakMap,G=M.createTreeWalker(M,129);function Z(t,e){if(!N(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==A?A.createHTML(e):e}const J=(t,e)=>{const i=t.length-1,r=[];let s,a=2===e?"<svg>":3===e?"<math>":"",n=O;for(let e=0;e<i;e++){const i=t[e];let o,l,d=-1,c=0;for(;c<i.length&&(n.lastIndex=c,l=n.exec(i),null!==l);)c=n.lastIndex,n===O?"!--"===l[1]?n=T:void 0!==l[1]?n=R:void 0!==l[2]?(L.test(l[2])&&(s=RegExp("</"+l[2],"g")),n=D):void 0!==l[3]&&(n=D):n===D?">"===l[0]?(n=s??O,d=-1):void 0===l[1]?d=-2:(d=n.lastIndex-l[2].length,o=l[1],n=void 0===l[3]?D:'"'===l[3]?W:z):n===W||n===z?n=D:n===T||n===R?n=O:(n=D,s=void 0);const h=n===D&&t[e+1].startsWith("/>")?" ":"";a+=n===O?i+P:d>=0?(r.push(o),i.slice(0,d)+E+i.slice(d)+C+h):i+C+(-2===d?e:h)}return[Z(t,a+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),r]};class Y{constructor({strings:t,_$litType$:e},i){let r;this.parts=[];let s=0,a=0;const n=t.length-1,o=this.parts,[l,d]=J(t,e);if(this.el=Y.createElement(l,i),G.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(r=G.nextNode())&&o.length<n;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(E)){const e=d[a++],i=r.getAttribute(t).split(C),n=/([.?@])?(.*)/.exec(e);o.push({type:1,index:s,name:n[2],strings:i,ctor:"."===n[1]?it:"?"===n[1]?rt:"@"===n[1]?st:et}),r.removeAttribute(t)}else t.startsWith(C)&&(o.push({type:6,index:s}),r.removeAttribute(t));if(L.test(r.tagName)){const t=r.textContent.split(C),e=t.length-1;if(e>0){r.textContent=k?k.emptyScript:"";for(let i=0;i<e;i++)r.append(t[i],U()),G.nextNode(),o.push({type:2,index:++s});r.append(t[e],U())}}}else if(8===r.nodeType)if(r.data===S)o.push({type:2,index:s});else{let t=-1;for(;-1!==(t=r.data.indexOf(C,t+1));)o.push({type:7,index:s}),t+=C.length-1}s++}}static createElement(t,e){const i=M.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,r){if(e===F)return e;let s=void 0!==r?i._$Co?.[r]:i._$Cl;const a=I(e)?void 0:e._$litDirective$;return s?.constructor!==a&&(s?._$AO?.(!1),void 0===a?s=void 0:(s=new a(t),s._$AT(t,i,r)),void 0!==r?(i._$Co??=[])[r]=s:i._$Cl=s),void 0!==s&&(e=Q(t,s._$AS(t,e.values),s,r)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,r=(t?.creationScope??M).importNode(e,!0);G.currentNode=r;let s=G.nextNode(),a=0,n=0,o=i[0];for(;void 0!==o;){if(a===o.index){let e;2===o.type?e=new tt(s,s.nextSibling,this,t):1===o.type?e=new o.ctor(s,o.name,o.strings,this,t):6===o.type&&(e=new at(s,this,t)),this._$AV.push(e),o=i[++n]}a!==o?.index&&(s=G.nextNode(),a++)}return G.currentNode=M,r}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,r){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),I(t)?t===V||null==t||""===t?(this._$AH!==V&&this._$AR(),this._$AH=V):t!==this._$AH&&t!==F&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>N(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==V&&I(this._$AH)?this._$AA.nextSibling.data=t:this.T(M.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,r="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=Y.createElement(Z(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===r)this._$AH.p(e);else{const t=new X(r,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=K.get(t.strings);return void 0===e&&K.set(t.strings,e=new Y(t)),e}k(t){N(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,r=0;for(const s of t)r===e.length?e.push(i=new tt(this.O(U()),this.O(U()),this,this.options)):i=e[r],i._$AI(s),r++;r<e.length&&(this._$AR(i&&i._$AB.nextSibling,r),e.length=r)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=w(t).nextSibling;w(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,r,s){this.type=1,this._$AH=V,this._$AN=void 0,this.element=t,this.name=e,this._$AM=r,this.options=s,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=V}_$AI(t,e=this,i,r){const s=this.strings;let a=!1;if(void 0===s)t=Q(this,t,e,0),a=!I(t)||t!==this._$AH&&t!==F,a&&(this._$AH=t);else{const r=t;let n,o;for(t=s[0],n=0;n<s.length-1;n++)o=Q(this,r[i+n],e,n),o===F&&(o=this._$AH[n]),a||=!I(o)||o!==this._$AH[n],o===V?t=V:t!==V&&(t+=(o??"")+s[n+1]),this._$AH[n]=o}a&&!r&&this.j(t)}j(t){t===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class it extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===V?void 0:t}}class rt extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==V)}}class st extends et{constructor(t,e,i,r,s){super(t,e,i,r,s),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??V)===F)return;const i=this._$AH,r=t===V&&i!==V||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,s=t!==V&&(i===V||r);r&&this.element.removeEventListener(this.name,this,i),s&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class at{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const nt=x.litHtmlPolyfillSupport;nt?.(Y,tt),(x.litHtmlVersions??=[]).push("3.3.3");const ot=globalThis;class lt extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const r=i?.renderBefore??e;let s=r._$litPart$;if(void 0===s){const t=i?.renderBefore??null;r._$litPart$=s=new tt(e.insertBefore(U(),t),t,void 0,i??{})}return s._$AI(t),s})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return F}}lt._$litElement$=!0,lt.finalized=!0,ot.litElementHydrateSupport?.({LitElement:lt});const dt=ot.litElementPolyfillSupport;dt?.({LitElement:lt}),(ot.litElementVersions??=[]).push("4.2.2");const ct="—";function ht(t,e,i,r){const s={minimumFractionDigits:i,maximumFractionDigits:r};let a;try{a=new Intl.NumberFormat(t,s)}catch(t){if(!(t instanceof RangeError))throw t;a=new Intl.NumberFormat("en",s)}return a.format(e).replace(/[  ]/g," ")}function pt(t){const e=/^(\d{4})-(\d{2})-(\d{2})/.exec(t);return e?`${e[3]}/${e[2]}/${e[1]}`:t}function ut(t,e){const i=pt(t),r=pt(e);return t.slice(0,4)===e.slice(0,4)?`${i.slice(0,5)} – ${r}`:`${i} – ${r}`}function _t(t,e){return null===e?ct:`${ht(t,e,0,2)} kWh`}function mt(t,e){return null===e?ct:`${ht(t,e,2,2)} €`}function gt(t,e){return null===e?ct:`${ht(t,e,4,4)} €/kWh`}function vt(t,e){return null===e?ct:`${ht(t,e,1,1)} %`}function $t(t,e,i){if(null===e)return ct;const r="kwh"===i?"kWh":"€",s="kwh"===i?[0,2]:[2,2],a=ht(t,Math.abs(e),...s);return`${0===Number(Math.abs(e).toFixed(s[1]))?"":e<0?"−":"+"}${a} ${r}`}function yt(t,e){return null===e?ct:`${ht(t,e,0,2)} m³`}function ft(t,e){return null===e?ct:`${ht(t,e,0,2)} %`}const bt={es:{pill_estimated:"estimada",pill_unreadable:"no se pudo leer",tab_electricity:"Luz",tab_gas:"Gas",col_period:"Periodo",col_kwh_invoice:"kWh factura",col_kwh_edata:"kWh Datadis",col_delta_kwh:"Δ kWh",col_amount:"Importe",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Potencia + energía: factura {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Comparada junto con: {numbers}",detail_in_group_of:"Regularizada en la factura {number}",detail_vat:"IVA {rate} sobre {base}: {amount}",detail_energy_price:"Precio de la energía: {price}",detail_meter_current:"Lectura actual ({kind}, {date})",detail_meter_previous:"Lectura anterior ({kind}, {date})",meter_title:"Última lectura facturada",meter_since_previous:"{diff} desde la anterior ({value}, {kind}, {date})",meter_real:"real",meter_estimated:"estimada",meter_p1:"P1 (punta)",meter_p2:"P2 (llano)",meter_p3:"P3 (valle)",detail_period_row:"{period}: factura {invoice} / Datadis {edata}",row_covers:"abarca {n} facturas",detail_own_kwh:"Esta factura: {kwh}",detail_group_heading:"Comparación del grupo ({n} facturas)",card_title:"Facturas",loading:"Cargando…",empty:"Todavía no hay facturas",error:"No se pudieron cargar las facturas",card_description:"Facturas de CurEnergía comparadas con los datos de Datadis",chart_title:"kWh por factura",chart_empty:"Sin datos para el gráfico",chart_invoice:"Factura",chart_datadis:"Datadis",panel_title:"Facturas",panel_menu:"Menú",panel_billed_12m:"Facturado en 12 meses",panel_kwh_delta:"kWh factura vs Datadis",panel_estimated_count:"Lecturas estimadas",panel_unreadable:"Correos con factura que no se pudo leer: {n}",panel_unsupported:"Correos con factura no soportada (rectificativa o abono) o demasiado grande (más de 15 MB): {n}",panel_mail_error:"No se pudo leer el correo; se muestran las facturas guardadas",editor_title:"Título",editor_supply:"Pestaña inicial",editor_max_invoices:"Número máximo de facturas",editor_entry_id:"Cuenta de correo (opcional)"},en:{pill_estimated:"estimated",pill_unreadable:"could not be read",tab_electricity:"Electricity",tab_gas:"Gas",col_period:"Period",col_kwh_invoice:"Invoice kWh",col_kwh_edata:"Datadis kWh",col_delta_kwh:"Δ kWh",col_amount:"Amount",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Power + energy: invoice {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Compared together with: {numbers}",detail_in_group_of:"Settled by invoice {number}",detail_vat:"VAT {rate} on {base}: {amount}",detail_energy_price:"Energy price: {price}",detail_meter_current:"Current reading ({kind}, {date})",detail_meter_previous:"Previous reading ({kind}, {date})",meter_title:"Latest billed reading",meter_since_previous:"{diff} since the previous one ({value}, {kind}, {date})",meter_real:"measured",meter_estimated:"estimated",meter_p1:"P1 (peak)",meter_p2:"P2 (standard)",meter_p3:"P3 (off-peak)",detail_period_row:"{period}: invoice {invoice} / Datadis {edata}",row_covers:"covers {n} invoices",detail_own_kwh:"This invoice: {kwh}",detail_group_heading:"Group comparison ({n} invoices)",card_title:"Invoices",loading:"Loading…",empty:"No invoices yet",error:"Could not load the invoices",card_description:"CurEnergía invoices compared with Datadis data",chart_title:"kWh per invoice",chart_empty:"No data for the chart",chart_invoice:"Invoice",chart_datadis:"Datadis",panel_title:"Invoices",panel_menu:"Menu",panel_billed_12m:"Billed in 12 months",panel_kwh_delta:"Invoice kWh vs Datadis",panel_estimated_count:"Estimated readings",panel_unreadable:"E-mails with an invoice that could not be read: {n}",panel_unsupported:"E-mails with an invoice that is not supported (corrective or credit note) or too large (over 15 MB): {n}",panel_mail_error:"Could not read the mailbox; showing the saved invoices",editor_title:"Title",editor_supply:"Initial tab",editor_max_invoices:"Maximum number of invoices",editor_entry_id:"Mail account (optional)"}};function xt(t){return t.locale?.language||t.language||"en"}function wt(t,e,i){return kt(xt(t),e,i)}function kt(t,e,i){const r=(t.toLowerCase().startsWith("es")?bt.es:bt.en)[e];return i?r.replace(/\{(\w+)\}/g,(t,e)=>e in i?String(i[e]):t):r}const At=[{supply:"electricity",label:"tab_electricity"},{supply:"gas",label:"tab_gas"}],Et=[{key:"p1",name:"P1"},{key:"p2",name:"P2"},{key:"p3",name:"P3"}],Ct=[{key:"p1",label:"meter_p1"},{key:"p2",label:"meter_p2"},{key:"p3",label:"meter_p3"}];function St(t,e){return e.period_end.localeCompare(t.period_end)||e.issue_date.localeCompare(t.issue_date)||e.number.localeCompare(t.number)}class Pt extends lt{constructor(){super(),this.contracts=[],this.supply="electricity",this._expanded=new Set}render(){const t=(this.contracts??[]).filter(t=>t.supply===this.supply);return q`
      <div class="tabs" role="tablist">
        ${At.map(({supply:t,label:e})=>q`
            <button
              class="tab"
              role="tab"
              type="button"
              aria-selected=${t===this.supply?"true":"false"}
              @click=${()=>this._selectSupply(t)}
            >
              ${wt(this.hass,e)}
            </button>
          `)}
      </div>
      ${0===t.length?q`<div class="empty">${wt(this.hass,"empty")}</div>`:t.map(e=>this._renderContract(e,t.length>1))}
    `}_renderContract(t,e){const i=[...t.invoices].sort(St),r=this.maxInvoices,s=r&&r>0?i.slice(0,r):i,a="gas"===this.supply?["col_period","col_kwh","col_m3","col_amount","col_price_kwh"]:["col_period","col_kwh_invoice","col_kwh_edata","col_delta_kwh","col_amount","col_delta_eur"];return q`
      ${e?q`<h3 class="contract-name">${t.name}</h3>`:V}
      ${this._renderMeter((n=i,n.find(t=>t.meter&&"no_leida"!==t.status)?.meter??null))}
      <div class="scroll">
        <table>
          <thead>
            <tr>
              ${a.map(t=>q`<th>${wt(this.hass,t)}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${s.map(e=>this._renderRow(t,e,a.length))}
          </tbody>
        </table>
      </div>
    `;var n}_meterKind(t){return wt(this.hass,t?"meter_estimated":"meter_real")}_renderMeter(t){if(!t)return V;const e=xt(this.hass),i=t.previous,r=q`<span class="pill">${this._meterKind(t.estimated)}</span>`;return q`
      <div class="meter">
        <div class="meter-note">${wt(this.hass,"meter_title")}</div>
        ${null!==t.m3?q`<div class="meter-value">${yt(e,t.m3)} ${r}</div>
              <div class="meter-note">
                ${pt(t.read_on)}
                ${i&&null!==i.m3?q`·
                    ${wt(this.hass,"meter_since_previous",{diff:yt(e,t.m3-i.m3),value:yt(e,i.m3),kind:this._meterKind(i.estimated),date:pt(i.read_on)})}`:V}
              </div>`:q`<div class="meter-note">${pt(t.read_on)} ${r}</div>
              <div class="meter-periods">
                ${Ct.map(({key:i,label:r})=>q`<div>
                      <span class="meter-note">${wt(this.hass,r)}</span>
                      <strong>${_t(e,t.periods?.[i]??null)}</strong>
                    </div>`)}
              </div>`}
      </div>
    `}_renderMeterDetail(t){const e=xt(this.hass),i=t.previous,r=wt(this.hass,"detail_meter_current",{kind:this._meterKind(t.estimated),date:pt(t.read_on)});return null===t.m3?q`<div>${r}</div>
        <ul>
          ${Ct.map(({key:i,label:r})=>q`<li>
                <span>${wt(this.hass,r)}</span>
                <span>${_t(e,t.periods?.[i]??null)}</span>
              </li>`)}
        </ul>`:q`<ul>
      <li><span>${r}</span><span>${yt(e,t.m3)}</span></li>
      ${i?q`<li>
            <span>
              ${wt(this.hass,"detail_meter_previous",{kind:this._meterKind(i.estimated),date:pt(i.read_on)})}
            </span>
            <span>${yt(e,i.m3)}</span>
          </li>`:V}
    </ul>`}_renderRow(t,e,i){const r=xt(this.hass),s=`${t.entry_id}|${t.contract}|${e.number}`,a=this._expanded.has(s),n=e.comparison?.group.length??0,o="color: var(--secondary-text-color)",l=null==e.comparison?.delta_kwh?o:`color: var(${function(t){switch(t){case"ok":return"--success-color";case"no_cuadra":return"--warning-color";case"no_leida":return"--error-color";default:return"--secondary-text-color"}}(e.status)})`,d=q`
      <td>
        <button class="toggle" type="button" aria-expanded=${a?"true":"false"}>
          ${ut(e.period_start,e.period_end)}
          ${e.estimated?q`<span class="pill">${wt(this.hass,"pill_estimated")}</span>`:V}
          ${"no_leida"===e.status?q`<span class="pill error">${wt(this.hass,"pill_unreadable")}</span>`:V}
          ${n>1?q`<span class="note">${wt(this.hass,"row_covers",{n:n})}</span>`:V}
        </button>
      </td>
    `,c=e.comparison,h="gas"===e.supply?q`
            <td>${_t(r,e.kwh)}</td>
            <td>${yt(r,e.m3)}</td>
            <td>${mt(r,e.total)}</td>
            <td>${gt(r,e.price_kwh)}</td>
          `:q`
            <td>${_t(r,c?.invoice_kwh??e.kwh)}</td>
            <td>${_t(r,c?.edata_kwh??null)}</td>
            <td style=${l}>${$t(r,c?.delta_kwh??null,"kwh")}</td>
            <td>${mt(r,e.total)}</td>
            <td style=${o}>${$t(r,c?.delta_eur??null,"eur")}</td>
          `;return q`
      <tr class="row ${e.estimated?"estimated":""}" @click=${()=>this._toggle(s)}>
        ${d} ${h}
      </tr>
      ${a?q`<tr class="detail">
            <td colspan=${i}>${this._renderDetail(e)}</td>
          </tr>`:V}
    `}_renderDetail(t){const e=xt(this.hass),i="gas"!==t.supply,r=t.comparison;return q`
      <div class="detail-body">
        <ul>
          ${t.concepts.map(t=>q`<li><span>${t.label}</span><span>${mt(e,t.amount)}</span></li>`)}
        </ul>
        <div>
          ${wt(this.hass,"detail_vat",{rate:ft(e,t.vat.rate),base:mt(e,t.vat.base),amount:mt(e,t.vat.amount)})}
        </div>
        ${i?this._renderElectricityDetail(t,r):V}
        ${t.meter?this._renderMeterDetail(t.meter):V}
        ${t.in_group_of?q`<div>
              ${wt(this.hass,"detail_in_group_of",{number:t.in_group_of})}
            </div>`:V}
        ${r&&r.group.length>1?q`<div>
              ${wt(this.hass,"detail_group",{numbers:r.group.join(", ")})}
            </div>`:V}
      </div>
    `}_renderElectricityDetail(t,e){const i=xt(this.hass),r=e?.invoice_periods??t.periods,s=e?.edata_periods??null,a=null!==r||null!==s,n=(e?.group.length??0)>1;return q`
      ${n?q`<div>${wt(this.hass,"detail_own_kwh",{kwh:_t(i,t.kwh)})}</div>
            <strong>
              ${wt(this.hass,"detail_group_heading",{n:e?.group.length??0})}
            </strong>`:V}
      ${a?q`<ul>
            ${Et.map(({key:t,name:e})=>q`<li>
                  ${wt(this.hass,"detail_period_row",{period:e,invoice:_t(i,r?.[t]??null),edata:_t(i,s?.[t]??null)})}
                </li>`)}
          </ul>`:V}
      ${e?q`<div>
            ${wt(this.hass,"detail_power_energy",{invoice:mt(i,e.invoice_eur),edata:mt(i,e.edata_eur)})}
            (${wt(this.hass,"detail_delta_pct",{pct:vt(i,e.delta_pct)})})
          </div>`:V}
      <div>
        ${wt(this.hass,"detail_energy_price",{price:gt(i,t.energy_price_kwh)})}
      </div>
    `}_toggle(t){const e=new Set(this._expanded);e.delete(t)||e.add(t),this._expanded=e}_selectSupply(t){t!==this.supply&&(this.supply=t,this._expanded=new Set,this.dispatchEvent(new CustomEvent("supply-changed",{detail:{supply:t},bubbles:!0,composed:!0})))}}function Mt(t){return Object.fromEntries(Object.entries(t).filter(([,t])=>void 0!==t))}function Ut(t,e={}){return t.connection.sendMessagePromise(Mt({type:"curenergia/invoices",entry_id:e.entry_id,supply:e.supply}))}function It(t,e){return t.connection.sendMessagePromise(Mt({type:"curenergia/summary",entry_id:e}))}Pt.properties={hass:{attribute:!1},contracts:{attribute:!1},supply:{type:String},maxInvoices:{type:Number,attribute:"max-invoices"},_expanded:{state:!0}},Pt.styles=a`
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
    tr.row:focus-within {
      background: var(--secondary-background-color, transparent);
    }
    .toggle {
      appearance: none;
      background: none;
      border: none;
      color: inherit;
      cursor: pointer;
      font: inherit;
      margin: 0;
      padding: 0;
      text-align: left;
    }
    .toggle:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
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
    .meter {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      margin-bottom: 8px;
      padding: 10px 12px;
    }
    .meter-note {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .meter-value {
      font-size: 1.6em;
      font-weight: 500;
    }
    .meter-periods {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      margin-top: 4px;
    }
    .meter-periods strong {
      display: block;
      font-weight: 500;
    }
    @media (max-width: 450px) {
      th,
      td {
        padding: 6px 4px;
      }
    }
  `,customElements.get("curenergia-invoice-table")||customElements.define("curenergia-invoice-table",Pt);const Nt={title:"editor_title",supply:"editor_supply",max_invoices:"editor_max_invoices",entry_id:"editor_entry_id"};class Ht extends lt{constructor(){super(),this._requestId=0,this._onSupplyChanged=t=>{const e=t.detail?.supply;"electricity"!==e&&"gas"!==e||(this._supply=e)},this._failed=!1,this._supply="electricity"}static getStubConfig(){return{max_invoices:6}}static getConfigForm(){const t=document.documentElement.lang||navigator.language||"en";return{schema:[{name:"title",selector:{text:{}}},{name:"supply",selector:{select:{mode:"dropdown",options:[{value:"electricity",label:kt(t,"tab_electricity")},{value:"gas",label:kt(t,"tab_gas")}]}}},{name:"max_invoices",selector:{number:{min:1,max:60,mode:"box"}}},{name:"entry_id",selector:{config_entry:{integration:"curenergia"}}}],computeLabel:e=>{const i=Nt[e.name];return i?kt(t,i):void 0}}}get hass(){return this._hass}set hass(t){this._hass=t,this.requestUpdate(),this._start()}setConfig(t){const e=function(t){if(null===t||"object"!=typeof t||Array.isArray(t))throw new Error("Invalid configuration");const e=Object.fromEntries(Object.entries(t).filter(([,t])=>""!==t)),{max_invoices:i,supply:r,title:s,entry_id:a}=e;if(void 0!==i&&("number"!=typeof i||!Number.isInteger(i)||i<1||i>60))throw new Error("max_invoices must be an integer between 1 and 60");if(void 0!==r&&"electricity"!==r&&"gas"!==r)throw new Error('supply must be "electricity" or "gas"');if(void 0!==s&&"string"!=typeof s)throw new Error("title must be a string");if(void 0!==a&&"string"!=typeof a)throw new Error("entry_id must be a string");return e}(t),i=this._config;this._config=e,this._supply=e.supply??"electricity",i&&i.entry_id!==e.entry_id&&void 0!==this._timer&&this._load()}getCardSize(){const t=this._config?.max_invoices??6,e=(this._data??[]).filter(t=>t.supply===this._supply).reduce((t,e)=>t+e.invoices.length,0);return 3+Math.min(t,e)}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&this._config&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1}async _load(){const t=this._hass;if(!t)return;this._requestId+=1;const e=this._requestId;try{const i=await Ut(t,{entry_id:this._config?.entry_id});if(e!==this._requestId)return;this._data=i.contracts??[],this._failed=!1}catch{if(e!==this._requestId)return;this._failed=!0}}render(){const t=this._config,e=this._hass;return t&&e?q`
      <ha-card .header=${t.title??wt(e,"card_title")}>
        <div class="body">
          ${this._failed?q`<div class="message error">${wt(e,"error")}</div>`:V}
          ${void 0===this._data?this._failed?V:q`<div class="message">${wt(e,"loading")}</div>`:q`<curenergia-invoice-table
                .hass=${e}
                .contracts=${this._data}
                .supply=${this._supply}
                .maxInvoices=${t.max_invoices??6}
                @supply-changed=${this._onSupplyChanged}
              ></curenergia-invoice-table>`}
        </div>
      </ha-card>
    `:V}}Ht.properties={_config:{state:!0},_data:{state:!0},_failed:{state:!0},_supply:{state:!0}},Ht.styles=a`
    :host {
      display: block;
    }
    ha-card {
      display: block;
    }
    .body {
      padding: 0 16px 16px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-invoices-card")||customElements.define("curenergia-invoices-card",Ht);const Ot=window.customCards??=[];Ot.some(t=>"curenergia-invoices-card"===t.type)||Ot.push({type:"curenergia-invoices-card",name:"CurEnergía",description:bt.en.card_description,preview:!1,documentationURL:"https://github.com/yuuues/hacs-curenergia#readme"});const Tt=640,Rt=212;function Dt(t,e){const i=/^(\d{4})-(\d{2})-(\d{2})/.exec(t);if(!i)return t;const r=`${i[3]}/${i[2]}`;return e?`${r}/${i[1].slice(2)}`:r}function zt(t,e){const i=t.comparison;if(!i||null===i.edata_kwh)return null;if(i.group.length<=1)return i.edata_kwh;const r=e.filter(e=>e.in_group_of===t.number),s=i.group.filter(e=>e!==t.number);let a=i.edata_kwh;for(const t of s){const e=r.find(e=>e.number===t),i=e?.comparison?.edata_kwh??null;if(null===i)return null;a-=i}return Math.round(100*a)/100}function Wt(t){return"no_leida"===t.status?"unreadable":t.estimated?"estimated":null}function Lt(t,e){return t.period_end.localeCompare(e.period_end)||t.issue_date.localeCompare(e.issue_date)||t.number.localeCompare(e.number)}class jt extends lt{constructor(){super(),this.invoices=[]}_points(){const t=this.invoices.filter(t=>"electricity"===t.supply),e=[...t].sort(Lt).slice(-12),i=new Set(e.map(t=>t.period_end.slice(0,4))).size>1;return e.map(e=>({label:Dt(e.period_end,i),period:ut(e.period_start,e.period_end),invoice:e.kwh,datadis:zt(e,t),mark:Wt(e)}))}render(){const t=this.hass;if(!t)return V;const e=xt(t),i=this._points(),r=i.flatMap(t=>[t.invoice,t.datadis].filter(t=>null!==t));if(0===r.length)return q`<div class="message">${wt(t,"chart_empty")}</div>`;const s=Math.max(...r,0),a=568/i.length,n=Math.min(.36*a,26),o=wt(t,"chart_invoice"),l=wt(t,"chart_datadis"),d=(i,r,a,d)=>{const c=(t=>s>0?Math.max(t,0)/s*196:0)(a),h="invoice"===i?o:l,p="invoice"===i?d.mark:null;return B`<rect
        class="bar ${i} ${p??""}"
        x=${r}
        y=${Rt-c}
        width=${n}
        height=${c}
        rx="2"
      ><title>${h} ${d.period}: ${_t(e,a)}${(e=>"estimated"===e?` (${wt(t,"pill_estimated")})`:"unreadable"===e?` (${wt(t,"pill_unreadable")})`:"")(p)}</title></rect>`},c=new Set(i.map(t=>t.mark));return q`
      <div class="title">${wt(t,"chart_title")}</div>
      <svg
        viewBox="0 0 ${Tt} ${236}"
        role="img"
        aria-label=${wt(t,"chart_title")}
        preserveAspectRatio="xMidYMid meet"
      >
        <line class="grid" x1=${64} x2=${632} y1=${16} y2=${16} />
        <line
          class="axis"
          x1=${64}
          x2=${632}
          y1=${Rt}
          y2=${Rt}
        />
        <text class="y-label" x=${58} y=${20} text-anchor="end">${_t(e,s)}</text>
        ${i.map((t,e)=>{const i=64+a*e+a/2,r=null!==t.invoice&&null!==t.datadis;return B`
            ${null!==t.invoice?d("invoice",r?i-n-1:i-n/2,t.invoice,t):V}
            ${null!==t.datadis?d("datadis",null!==t.invoice?i+1:i-n/2,t.datadis,t):V}
            <text class="x-label" x=${i} y=${228} text-anchor="middle">${t.label}</text>
          `})}
      </svg>
      <div class="legend">
        <span><i class="swatch invoice"></i>${o}</span>
        <span><i class="swatch datadis"></i>${l}</span>
        ${c.has("estimated")?q`<span><i class="swatch invoice estimated"></i>${wt(t,"pill_estimated")}</span>`:V}
        ${c.has("unreadable")?q`<span><i class="swatch invoice unreadable"></i>${wt(t,"pill_unreadable")}</span>`:V}
      </div>
    `}}jt.properties={hass:{attribute:!1},invoices:{attribute:!1}},jt.styles=a`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .title {
      font-weight: 500;
      margin: 8px 0;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .axis {
      stroke: var(--divider-color);
      stroke-width: 1;
    }
    .grid {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 3 3;
    }
    text {
      fill: var(--secondary-text-color);
      font-size: 11px;
    }
    .bar.invoice {
      fill: var(--primary-color);
    }
    .bar.datadis {
      fill: var(--secondary-text-color);
    }
    /* Estimated or unreadable invoice figure: lighter fill and dashed outline. */
    .bar.invoice.estimated,
    .bar.invoice.unreadable {
      fill-opacity: 0.35;
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 3 2;
    }
    .bar.invoice.unreadable {
      stroke: var(--error-color);
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin: 4px 0 8px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .swatch {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }
    .swatch.invoice {
      background: var(--primary-color);
    }
    .swatch.datadis {
      background: var(--secondary-text-color);
    }
    .swatch.invoice.estimated,
    .swatch.invoice.unreadable {
      background: transparent;
      border: 1.5px dashed var(--primary-color);
      box-sizing: border-box;
    }
    .swatch.invoice.unreadable {
      border-color: var(--error-color);
    }
  `,customElements.get("curenergia-bar-chart")||customElements.define("curenergia-bar-chart",jt);class qt extends lt{constructor(){super(),this._requestId=0,this._inFlight=!1,this._onSupplyChanged=t=>{const e=t.detail?.supply;"electricity"!==e&&"gas"!==e||(this._supply=e)},this._toggleMenu=()=>{this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:!0,composed:!0}))},this.narrow=!1,this._failed=!1,this._supply="electricity"}get hass(){return this._hass}set hass(t){this._hass=t,this.requestUpdate(),this._start()}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1,this._inFlight=!1}async _load(){const t=this._hass;if(!t||this._inFlight)return;this._inFlight=!0,this._requestId+=1;const e=this._requestId;try{const[i,r]=await Promise.all([It(t),Ut(t)]);if(e!==this._requestId)return;this._summary=i,this._data=r.contracts??[],this._failed=!1}catch{if(e!==this._requestId)return;this._failed=!0}finally{e===this._requestId&&(this._inFlight=!1)}}_renderMenuButton(t){return customElements.get("ha-menu-button")?q`<ha-menu-button .hass=${t} .narrow=${this.narrow}></ha-menu-button>`:this.narrow?q`<button
      class="menu"
      type="button"
      aria-label=${wt(t,"panel_menu")}
      @click=${this._toggleMenu}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z" />
      </svg>
    </button>`:V}_renderKpis(t){const e=xt(t),i=this._summary,r=(t,e)=>q`<div class="kpi">
        <div class="value">${e}</div>
        <div class="label">${t}</div>
      </div>`;return q`<div class="kpis">
      ${r(wt(t,"panel_billed_12m"),mt(e,i?.billed_12m??null))}
      ${r(wt(t,"panel_kwh_delta"),function(t,e){if(null===e)return ct;const i=ht(t,Math.abs(e),1,1);return`${0===Number(Math.abs(e).toFixed(1))?"":e<0?"−":"+"}${i} %`}(e,i?.kwh_delta_pct??null))}
      ${r(wt(t,"panel_estimated_count"),i?function(t,e){return ht(t,e,0,0)}(e,i.estimated_count):"—")}
    </div>`}_renderBody(t){if(void 0===this._data)return this._failed?q``:q`<div class="message">${wt(t,"loading")}</div>`;if(0===this._data.length)return q`<div class="message">${wt(t,"empty")}</div>`;const e=this._data.filter(t=>"electricity"===t.supply),i=e.length>1;return q`
      ${e.map(e=>q`
          <div class="section">
            ${i?q`<h3 class="chart-name">${e.name}</h3>`:V}
            <curenergia-bar-chart
              .hass=${t}
              .invoices=${e.invoices}
            ></curenergia-bar-chart>
          </div>
        `)}
      <div class="section">
        <curenergia-invoice-table
          .hass=${t}
          .contracts=${this._data}
          .supply=${this._supply}
          @supply-changed=${this._onSupplyChanged}
        ></curenergia-invoice-table>
      </div>
    `}render(){const t=this._hass;if(!t)return V;const e=this._summary;return q`
      <div class="toolbar">
        ${this._renderMenuButton(t)}
        <div class="title">${wt(t,"panel_title")}</div>
      </div>
      <div class="content">
        ${this._failed?q`<div class="message error">${wt(t,"error")}</div>`:V}
        ${this._renderKpis(t)}
        ${e?.mail_error?q`<div class="warning">${wt(t,"panel_mail_error")}</div>`:V}
        ${e&&e.unreadable_emails>0?q`<div class="warning">
              ${wt(t,"panel_unreadable",{n:e.unreadable_emails})}
            </div>`:V}
        ${e&&e.unsupported_emails>0?q`<div class="warning">
              ${wt(t,"panel_unsupported",{n:e.unsupported_emails})}
            </div>`:V}
        ${this._renderBody(t)}
      </div>
    `}}qt.properties={hass:{attribute:!1},narrow:{type:Boolean},panel:{attribute:!1},_data:{state:!0},_summary:{state:!0},_failed:{state:!0},_supply:{state:!0}},qt.styles=a`
    :host {
      display: block;
      min-height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: calc(56px + env(safe-area-inset-top, 0px));
      padding: 0 12px;
      padding-top: env(safe-area-inset-top, 0px);
      box-sizing: border-box;
      background: var(--app-header-background-color);
      color: var(--app-header-text-color, var(--primary-text-color));
    }
    .menu {
      appearance: none;
      background: none;
      border: none;
      border-radius: 50%;
      color: inherit;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      padding: 12px;
      box-sizing: border-box;
    }
    .menu:focus-visible {
      outline: 2px solid var(--primary-color);
    }
    .menu svg {
      width: 24px;
      height: 24px;
      fill: currentColor;
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }
    .kpi,
    .section {
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px;
    }
    .kpi .value {
      font-size: 1.8em;
      font-weight: 500;
    }
    .kpi .label {
      margin-top: 4px;
      color: var(--secondary-text-color);
    }
    .warning {
      padding: 8px 12px;
      border-left: 4px solid var(--warning-color);
      background: var(--card-background-color);
      border-radius: 4px;
    }
    .chart-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 0 0 4px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-panel")||customElements.define("curenergia-panel",qt);
